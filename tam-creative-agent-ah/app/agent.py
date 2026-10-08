import os
import logging
import google.auth
import google.cloud.logging
from google.cloud.logging_v2.handlers import CloudLoggingHandler
from dotenv import find_dotenv, load_dotenv
from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.cloud import bigquery

# Initialize Cloud Logging
client = google.cloud.logging.Client()
handler = CloudLoggingHandler(client)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(handler)
logging.info("Cloud Logging initialized for TAM Creative Co-Pilot")
handler.close()

load_dotenv(find_dotenv(usecwd=True), override=True)

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id or "qwiklabs-gcp-01-0c1b6057dacb")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-east1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "1")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_latest_trends_date() -> str:
    try:
        bq_client = bigquery.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))
        rows = bq_client.query(
            "SELECT MAX(refresh_date) AS d FROM `bigquery-public-data.google_trends.international_top_terms`"
        ).result()
        for r in rows:
            if r and r.d:
                return r.d.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Warning fetching refresh_date: {e}")
    return "2026-08-15"


LATEST_DATE = get_latest_trends_date()


# Custom Python Function Tool for TAM Readiness & ROI Quantification
def calculate_tam_readiness_score_and_roi(
    max_percent_gain: int,
    customer_industry: str,
    critical_gcp_workloads: int = 5,
) -> dict:
    """Calculates customer traffic surge risk score, recommended GCP scaling buffer, and TAM ROI metrics.

    Args:
        max_percent_gain: Highest percent_gain observed in BigQuery rising search terms (e.g. 250).
        customer_industry: The customer's industry sector (e.g. 'Retail', 'Media', 'Gaming', 'FinTech').
        critical_gcp_workloads: Number of production GCP workloads (default 5).

    Returns:
        dict: Quantified risk tier, scaling buffer recommendation, TAM hours saved, and downtime cost avoided.
    """
    if max_percent_gain >= 500:
        risk_tier = "CRITICAL (High Breakout Surge)"
        scaling_buffer_pct = 50
    elif max_percent_gain >= 200:
        risk_tier = "HIGH (Significant Regional Momentum)"
        scaling_buffer_pct = 35
    else:
        risk_tier = "MODERATE (Baseline Seasonal Traffic)"
        scaling_buffer_pct = 20

    annual_tam_hours_saved = round(2.5 * 52, 1)  # 2.5 hrs/week saved on manual EBR/event prep
    estimated_downtime_risk_avoided_usd = critical_gcp_workloads * 18500

    return {
        "customer_industry": customer_industry,
        "observed_max_percent_gain": f"{max_percent_gain}%",
        "surge_risk_tier": risk_tier,
        "recommended_gke_and_cloud_run_headroom_pct": f"+{scaling_buffer_pct}%",
        "recommended_bigquery_slot_autoscale_cap_pct": f"+{scaling_buffer_pct + 10}%",
        "tam_hours_saved_per_week": 2.5,
        "annualized_tam_hours_saved_per_account": annual_tam_hours_saved,
        "estimated_outage_and_overage_risk_avoided_usd": f"${estimated_downtime_risk_avoided_usd:,}",
    }


tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
creds, _ = google.auth.default()
bq_toolset = BigQueryToolset(
    credentials_config=BigQueryCredentialsConfig(credentials=creds),
    bigquery_tool_config=tool_config,
)

# Sub-Agent 1: Multi-Dataset BigQuery Analyst (Google Trends + Hacker News)
bq_analyst_agent = Agent(
    name="bq_trends_and_tech_analyst",
    model=GEMINI_MODEL,
    description=(
        "BigQuery SQL specialist that queries Google Trends (international_top_terms, "
        "international_top_rising_terms) and Hacker News (bigquery-public-data.hacker_news.full) "
        "to correlate regional search spikes with developer and tech community trends."
    ),
    instruction=f"""You are a BigQuery SQL Expert supporting Google Cloud TAMs.
You have access to two public datasets in `bigquery-public-data`:

1. Google Trends:
   - `bigquery-public-data.google_trends.international_top_terms` (columns: `term`, `rank`, `score`, `week`, `refresh_date`, `country_name`, `region_name`)
   - `bigquery-public-data.google_trends.international_top_rising_terms` (columns: `term`, `percent_gain`, `rank`, `score`, `week`, `refresh_date`, `country_name`, `region_name`)
   - MANDATORY RULE: Always filter with `WHERE refresh_date = '{LATEST_DATE}'` and include `LIMIT 10`.
   - Use full country names (e.g. 'Germany', 'United Kingdom', 'France', 'Canada').

2. Hacker News (`bigquery-public-data.hacker_news.full`):
   - Columns: `title` (STRING), `score` (INTEGER), `type` (STRING), `timestamp` (TIMESTAMP).
   - When checking tech community pulse, query:
     SELECT title, score FROM `bigquery-public-data.hacker_news.full` WHERE type = 'story' AND score > 100 ORDER BY timestamp DESC LIMIT 5;

Always execute your SQL via `execute_sql` and return the exact terms, `percent_gain` values, and top tech stories.""",
    tools=[bq_toolset],
)

# Sub-Agent 2: Live Google Cloud & Market Researcher
cloud_research_agent = Agent(
    name="tam_cloud_readiness_researcher",
    model=GEMINI_MODEL,
    description="Searches live Google Cloud architecture guides, release notes, and web news to provide TAM recommendations.",
    instruction="""You are a Google Cloud TAM Research Specialist.
Use `google_search` to investigate what real-world events are driving the trending search terms and look up specific Google Cloud best practices (GKE Autopilot HPA pre-scaling, Cloud CDN cache hit optimization, Cloud Armor rate limiting, BigQuery slot reservations) relevant to the customer's industry.""",
    tools=[google_search],
)

# Root Orchestrator Agent: TAM Executive Pulse & Readiness Co-Pilot
root_agent = Agent(
    name="tam_creative_copilot_ankitharsora",
    model=GEMINI_MODEL,
    description=(
        "Multi-agent TAM Co-Pilot that combines BigQuery public datasets (Google Trends + Hacker News), "
        "live Google Search, and a custom TAM ROI & Readiness calculator to generate proactive customer briefs."
    ),
    instruction=f"""You are the **TAM Executive Pulse & Cloud Readiness Co-Pilot**.
Your goal is to help Google Cloud Technical Account Managers (TAMs) proactively prepare customers for regional traffic surges and technical risks.

Follow this exact workflow for every user request:
1. Call `bq_trends_and_tech_analyst` to query BigQuery (`refresh_date = '{LATEST_DATE}'`) for the top and rising search terms in the target country, plus recent high-score tech stories from Hacker News.
2. Call `calculate_tam_readiness_score_and_roi` using the highest `percent_gain` returned from BigQuery (or 300 if not specified) and the customer's industry.
3. Call `tam_cloud_readiness_researcher` to get real-world context on the top trending topics and relevant GCP architectural best practices.
4. Present a clear, executive-ready **TAM Proactive Customer Readiness Brief** with these 4 sections:
   - 📊 **1. Live Regional Demand & Tech Pulse (BigQuery Data as of `{LATEST_DATE}`)**: Top & breakout terms with `% gain` + Hacker News tech pulse.
   - 🎯 **2. Quantified Surge Risk & ROI Scorecard**: Output from `calculate_tam_readiness_score_and_roi` (Risk Tier, Recommended GKE/Cloud Run Headroom %, BigQuery Slot Autoscale Cap %, TAM Hours Saved, and Estimated Outage Risk Avoided $).
   - 🛠️ **3. Proactive GCP Architecture & FinOps Action Plan**: 3 concrete recommendations across Compute (GKE/Cloud Run), Networking/Security (Cloud CDN/Cloud Armor), and Data (BigQuery FinOps).
   - 💬 **4. Ready-to-Send Customer Email Snippet**: A short 4-line proactive message the TAM can paste directly to their customer stakeholder.""",
    tools=[
        AgentTool(agent=bq_analyst_agent),
        AgentTool(agent=cloud_research_agent),
        calculate_tam_readiness_score_and_roi,
    ],
)

app = App(root_agent=root_agent, name="app")
