from __future__ import annotations
import time
import uuid
from datetime import datetime
from collections import Counter
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.config import settings
from app.database import Base, engine, get_db
from app.models import User, Conversation, Message, Ticket
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, ChatRequest, ChatResponse
from app.auth import hash_password, verify_password, create_token, get_current_user
from app.rag import rag_store
from app.agents import detect_intents, run_agent, aggregate, sentiment

app = FastAPI(title="Multi-Agent AI Customer Support Assistant",
              version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip()
                   for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    try:
        rag_store.load_or_build()
    except Exception as exc:
        print(f"[startup] RAG index deferred: {exc}")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "multi-agent-customer-support"}


@app.post("/api/auth/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(
        User.email == payload.email.lower()))
    if existing:
        raise HTTPException(409, "Email is already registered")
    user = User(email=payload.email.lower(),
                password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_token(user.id))


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return TokenResponse(access_token=create_token(user.id))


def get_or_create_conversation(db, user, conversation_id, first_message):
    if conversation_id:
        conv = db.scalar(select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user.id
        ))
        if not conv:
            raise HTTPException(404, "Conversation not found")
        return conv
    conv = Conversation(
        user_id=user.id,
        title=first_message.strip().replace(
            "\n", " ")[:60] or "New conversation",
        session_id=str(uuid.uuid4())
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    started = time.perf_counter()
    conv = get_or_create_conversation(
        db, user, payload.conversation_id, payload.message)

    db.add(Message(conversation_id=conv.id, role="user", content=payload.message))
    db.commit()

    history_rows = db.scalars(
        select(Message).where(Message.conversation_id ==
                              conv.id).order_by(Message.created_at.asc())
    ).all()
    history = [{"role": m.role, "content": m.content}
               for m in history_rows[-8:]]

    agents = detect_intents(payload.message, history)

    retrieved = rag_store.search(payload.message, k=3)

    top_score = retrieved[0]["score"] if retrieved else 0.0

    results = [run_agent(agent, payload.message, retrieved, history)
               for agent in agents]
    answer = aggregate(payload.message, results)

    negative = sentiment(payload.message) == "negative"
    explicit = "HUMAN_ESCALATION_RECOMMENDED" in answer

    # Avoid escalating ordinary factual/product questions solely
    # because similarity score is modest.
    ordinary_information_query = (
        set(agents).issubset({"faq", "product"})
        and not negative
    )

    low_retrieval = (
        top_score < 0.22
        and not ordinary_information_query
    )

    complaint_unresolved = (
        "complaint" in agents
        and (
            negative
            or "escalate" in payload.message.lower()
            or "unresolved" in payload.message.lower()
        )
    )

    account_specific_issue = (
        any(a in agents for a in ["billing", "technical"])
        and any(
            phrase in payload.message.lower()
            for phrase in [
                "charged twice",
                "duplicate charge",
                "paid",
                "still locked",
                "unable to access"
            ]
        )
    )

    escalated = (
        explicit
        or low_retrieval
        or complaint_unresolved
        or account_specific_issue
    )
    clean_answer = answer.replace("HUMAN_ESCALATION_RECOMMENDED", "").strip()
    ticket_id = None
    if escalated:
        ticket = Ticket(
            conversation_id=conv.id,
            reason=f"Auto-escalated. Agents={','.join(agents)}; retrieval_top={top_score:.3f}"
        )
        db.add(ticket)
        db.flush()
        ticket_id = ticket.id
        clean_answer += "\n\nI have flagged this conversation for human support review."

    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    db.add(Message(
        conversation_id=conv.id, role="assistant", content=clean_answer,
        agents=",".join(agents), response_time_ms=elapsed_ms
    ))
    conv.updated_at = datetime.utcnow()
    db.commit()

    sources = []
    for r in retrieved[:4]:
        label = f"{r['source']} (page {r['page']})"
        if label not in sources:
            sources.append(label)

    return ChatResponse(
        conversation_id=conv.id, answer=clean_answer, agents=agents,
        retrieved_sources=sources, escalated=escalated, ticket_id=ticket_id,
        response_time_ms=elapsed_ms
    )


@app.get("/api/conversations")
def list_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Conversation).where(Conversation.user_id ==
                                   user.id).order_by(Conversation.updated_at.desc())
    ).all()
    return [{"id": c.id, "title": c.title, "session_id": c.session_id, "created_at": c.created_at, "updated_at": c.updated_at} for c in rows]


@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conv = db.scalar(select(Conversation).where(
        Conversation.id == conversation_id, Conversation.user_id == user.id
    ))
    if not conv:
        raise HTTPException(404, "Conversation not found")
    messages = db.scalars(
        select(Message).where(Message.conversation_id ==
                              conv.id).order_by(Message.created_at.asc())
    ).all()
    return {
        "id": conv.id, "title": conv.title, "session_id": conv.session_id,
        "messages": [{
            "id": m.id, "role": m.role, "content": m.content,
            "agents": [x for x in m.agents.split(",") if x],
            "response_time_ms": m.response_time_ms, "created_at": m.created_at
        } for m in messages]
    }


@app.get("/api/analytics")
def analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conv_ids = db.scalars(select(Conversation.id).where(
        Conversation.user_id == user.id)).all()
    if not conv_ids:
        return {"conversations": 0, "messages": 0, "agent_usage": {}, "avg_response_time_ms": 0, "open_tickets": 0}
    messages = db.scalars(select(Message).where(
        Message.conversation_id.in_(conv_ids))).all()
    assistant_msgs = [m for m in messages if m.role == "assistant"]
    usage = Counter()
    for m in assistant_msgs:
        for a in [x for x in m.agents.split(",") if x]:
            usage[a] += 1
    avg = sum(m.response_time_ms for m in assistant_msgs) / \
        len(assistant_msgs) if assistant_msgs else 0
    tickets = db.scalars(select(Ticket).where(
        Ticket.conversation_id.in_(conv_ids), Ticket.status == "open")).all()
    return {
        "conversations": len(conv_ids), "messages": len(messages),
        "agent_usage": dict(usage), "avg_response_time_ms": round(avg, 1),
        "open_tickets": len(tickets)
    }


@app.post("/api/rag/reindex")
def reindex(user: User = Depends(get_current_user)):
    rag_store.build()
    return {"status": "rebuilt", "chunks": len(rag_store.chunks)}
