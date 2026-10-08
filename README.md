# TAM Executive Pulse & Cloud Readiness Co-Pilot (tam-creative-agent-ah)

Built for the TAMtastic Gemini Enterprise (GE) Hackathon.

## Overview & Problem Statement
Google Cloud Technical Account Managers (TAMs) spend hours before Executive Business Reviews (EBRs) and peak-traffic readiness reviews correlating:
1. External consumer demand & market trends in the customer's region (to anticipate traffic spikes),
2. Quantitative Production Readiness & FinOps ROI metrics (Multi-region High Availability risk + Committed Use Discount optimization), and
3. Google Cloud architectural best practices (GKE, Cloud Armor, Spanner, FinOps).

The TAM Executive Pulse & Cloud Readiness Co-Pilot automates this entire workflow inside Gemini Enterprise using a multi-agent Google ADK architecture deployed on Vertex AI Agent Engine.

## Multi-Agent Architecture
- tam_executive_pulse_copilot (Root Orchestrator Agent - gemini-2.5-flash): Synthesizes findings from specialized sub-agents and tools into a structured TAM Executive Brief.
- bq_trends_and_tech_analyst (AgentTool + BigQueryToolset): NL2SQL specialist that queries bigquery-public-data.google_trends.international_top_terms and international_top_rising_terms with WriteMode.BLOCKED and partition pruning (refresh_date).
- tam_cloud_readiness_researcher (AgentTool + google_search): Researches live Google Cloud architecture best practices, release notes, and sector reliability patterns.
- calculate_tam_readiness_score_and_roi (Custom Python Function Tool): Computes a 0-100 TAM Readiness Score, Risk Tier (LOW, MEDIUM, HIGH), estimated annual FinOps savings (USD), and recommended TAM workstreams.

## Quickstart Commands
- Install & test locally: make install && make playground
- Deploy to Vertex AI Agent Engine: make backend
- Register with Gemini Enterprise: make register-gemini-enterprise
