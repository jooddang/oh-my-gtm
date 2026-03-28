"""Application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Runtime configuration for the application."""

    model_config = SettingsConfigDict(env_prefix="OH_MY_GTM_", extra="ignore")

    app_name: str = Field(default="oh-my-gtm")
    env: str = Field(default="local")
    database_url: str = Field(default="sqlite+pysqlite:///./oh_my_gtm.db")
    default_email_mode: str = Field(default="auto_send")
    default_linkedin_mode: str = Field(default="compliance_manual")
    max_daily_email_sends: int = Field(default=50, ge=1)
    max_daily_linkedin_preps: int = Field(default=25, ge=1)
    human_review_for_high_risk: bool = Field(default=True)
    openai_api_key: str | None = Field(default=None)
    openai_base_url: str = Field(default="https://api.openai.com/v1")
    openai_model: str = Field(default="gpt-5")
    llm_enabled: bool = Field(default=True)
    output_dir: str = Field(default="output")
    linkedin_browser_profile_dir: str = Field(default="output/linkedin-profile")
    linkedin_search_headless: bool = Field(default=True)
    daemon_poll_interval_seconds: int = Field(default=15, ge=1)
    daemon_max_search_queries: int = Field(default=4, ge=1)
    daemon_max_search_results_per_query: int = Field(default=5, ge=1)
    daemon_max_email_drafts: int = Field(default=5, ge=1)
    linkedin_collection_strategy: str = Field(default="auto")
    chrome_app_name: str = Field(default="Google Chrome")


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
