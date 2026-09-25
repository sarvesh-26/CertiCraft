from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Bulk Certificate Generator"
    database_url: str = "sqlite:///./certificates.db"
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 60
    storage_dir: str = "./storage"
    max_batch_size: int = 10000
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
