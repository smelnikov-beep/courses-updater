from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    main_admin_id: int
    main_admin_username: str
    second_admin_id: int
    default_link: str
    bot_token: str
    db_url: str
    db_url_local: str = ""
    database_name: str
    database_username: str
    database_password: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Settings()
