from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, description="Username for login")
    password: str = Field(..., min_length=6, description="Password for login")


class UserSession(BaseModel):
    id: int
    username: str
    role: str
