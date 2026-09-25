from pydantic import BaseModel
class JobResponse(BaseModel):
    id: int
    status: str
    total: int
    processed: int
    succeeded: int
    failed: int
    error_message: str | None = None
