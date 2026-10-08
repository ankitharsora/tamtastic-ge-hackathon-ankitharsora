import os
import logging
import google.cloud.logging
from google.cloud.logging_v2.handlers import CloudLoggingHandler
from dotenv import find_dotenv, load_dotenv
from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools import google_search

client = google.cloud.logging.Client()
handler = CloudLoggingHandler(client)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(handler)
logging.info("Cloud Logging initialized for ADK agent script")
handler.close()

load_dotenv(find_dotenv(usecwd=True), override=True)

root_agent = Agent(
    name="basic_search_agent_ankitharsora",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    description="Agent to answer questions using Google Search.",
    instruction="I can answer your questions by searching the internet. Just ask me anything!",
    tools=[google_search],
)

app = App(root_agent=root_agent, name="app")
