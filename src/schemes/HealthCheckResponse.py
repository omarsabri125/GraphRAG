from pydantic import BaseModel

class HealthCheckSuccess(BaseModel):
    status: str
    app_name: str

class HealthCheckError(BaseModel):
    status: str
    message: str

