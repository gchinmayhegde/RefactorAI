from pydantic import BaseModel

class RefactorRequest(BaseModel):
    legacy_code: str
    source_language: str
    target_language: str = "python"

class Metrics(BaseModel):
    pre_complexity: int
    post_complexity: int
    tokens_used: int
    ai_cost_estimate: float