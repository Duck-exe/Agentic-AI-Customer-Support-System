from app.agents import detect_intents
from app.rag import chunk_text

def test_billing_route():
    assert "billing" in detect_intents("I was charged twice for my subscription")

def test_technical_route():
    assert "technical" in detect_intents("I cannot login because password reset gives an error")

def test_multi_agent_route():
    agents = detect_intents("I paid yesterday but Premium is still locked")
    assert "billing" in agents
    assert "technical" in agents

def test_complaint_route():
    assert "complaint" in detect_intents("This is unacceptable, I want to escalate my complaint")

def test_chunking():
    chunks = chunk_text("A sentence. " * 200, size=250, overlap=50)
    assert len(chunks) > 1
