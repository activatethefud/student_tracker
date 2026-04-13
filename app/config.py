from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Student Tracker"
    db_path: str = "student_tracker.db"
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    master_password: str = "RESET-admin-2024"

    class Config:
        env_file = ".env"


settings = Settings()