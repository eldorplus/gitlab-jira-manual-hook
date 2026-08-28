from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "gitlab-jira-manual-hook"
    environment: str = "development"
    log_level: str = "INFO"
    webhook_secret: str = "change-me"
    database_url: str = "postgresql://manualhook:manualhook@localhost:5432/manualhook"
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = "OPS"
    jira_issue_type: str = "Task"
    project_config: str = "config/projects.yml"
    elasticsearch_url: str = ""
    elasticsearch_api_key: str = ""
    elasticsearch_index_prefix: str = "gitlab-pipelines"
    elasticsearch_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
