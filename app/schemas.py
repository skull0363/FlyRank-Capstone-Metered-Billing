from pydantic import BaseModel
from typing import Optional

class TokenUsage(BaseModel):
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0

class GenerateRequest(BaseModel):
    tenant_id: str
    tokens: Optional[TokenUsage] = None   # omit for a plain API-call billable action