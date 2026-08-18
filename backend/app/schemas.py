from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    agents: list[str]
    retrieved_sources: list[str]
    escalated: bool
    ticket_id: Optional[int] = None
    response_time_ms: float
