import os
import google.auth
from dotenv import find_dotenv, load_dotenv
from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from .utils import get_latest_refresh_date, load_nl2sql_with_few_shot_prompt

load_dotenv(find_dotenv(usecwd=True), override=True)

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id or "qwiklabs-gcp-01-0c1b6057dacb")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-east1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "1")

AGENT_NAME = os.getenv("AGENT_NAME", "google_trends_bq_ankitharsora")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)
bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config, bigquery_tool_config=tool_config
)

latest_date = get_latest_refresh_date() or "2026-10-07"
agent_instruction = load_nl2sql_with_few_shot_prompt(
    refresh_date_value=latest_date
)

root_agent = Agent(
    model=GEMINI_MODEL,
    name=AGENT_NAME,
    description=(
        "A BigQuery SQL expert that answers natural language questions about "
        "top trending and rising international terms, according to Google search queries."
    ),
    instruction=agent_instruction,
    tools=[bigquery_toolset],
)

app = App(root_agent=root_agent, name="app")
