from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    NODE_BACKEND_URL: str = "http://localhost:3000"
    WORKER_TIMEOUT: int = 300

    class Config:
        env_file = ".env"

settings = Settings() 