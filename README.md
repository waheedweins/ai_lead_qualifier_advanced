# AI Lead Qualifier v2 🚀

Production-grade AI-powered lead generation, enrichment, scoring, and outreach system.

## Full Pipeline

```
POST /scrape/run?query=solar+installers+lahore&source=all
         │
         ├─── Google Maps (Apify) ──┐
         │                          ├─→ Lead Ingestor → PostgreSQL
         └─── Apollo.io ────────────┘
                                         │
                                         ▼
                                  Apollo Enrichment
                                  (phone, website, title)
                                         │
                                         ▼
                                  Tavily Web Search
                                  (online presence summary)
                                         │
                                         ▼
                                  Gemini AI Scoring
                                  (0-100 score + reason)
                                         │
                                    ┌────┴────┐
                                   HOT       COLD
                                  (≥50)     (<50)
                                    │
                                    ▼
                             Gemini writes
                          personalised message
                                    │
                              ┌─────┴─────┐
                           WhatsApp     Email
                          (if phone)  (SendGrid)
```

## What's New in v2

| Feature | v1 | v2 |
|---------|----|----|
| AI scoring | Heuristic rules | **Gemini 2.0 Flash** |
| Website enrichment | ✗ | **Tavily search** |
| Apollo.io integration | ✗ | **✓ people + company search** |
| Outreach messages | Template string | **Gemini-personalised** |
| WhatsApp fallback | ✗ | **Falls back to email** |
| Phone normalisation | ✗ | **E.164 auto-format** |
| Pipeline endpoint | ✗ | **POST /scrape/run** |
| Stats endpoint | ✗ | **GET /leads/stats** |
| Rescore endpoint | ✗ | **POST /leads/{id}/score** |
| Placeholder emails | Ingested | **Filtered out** |
| ai_reason in DB | ✗ | **✓ stored per lead** |

## Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/waheedweins/ai_lead_qualifier
cd ai_lead_qualifier

# 2. Set up env
cp .env.example .env
# Fill in your keys (Gemini is free, Tavily is free)

# 3. Run
docker-compose up --build

# 4. Test full pipeline
curl -X POST "http://localhost:8000/scrape/run?query=solar+installers+lahore&source=all"

# 5. Check leads
curl http://localhost:8000/leads/
curl http://localhost:8000/leads/stats
```

## AWS Secrets Manager

Add all keys to `production/LeadQualifier`:

```json
{
  "DATABASE_URL": "postgresql://...",
  "APIFY_API_TOKEN": "apify_api_...",
  "APOLLO_API_KEY": "your_apollo_key",
  "GEMINI_API_KEY": "AIzaSy...",
  "TAVILY_API_KEY": "tvly-...",
  "SENDGRID_API_KEY": "SG...",
  "EMAIL_FROM": "outreach@yourdomain.com",
  "WHATSAPP_TOKEN": "EAAxx...",
  "WHATSAPP_PHONE_ID": "123456789"
}
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/` | Health check |
| POST | `/scrape/?query=...&source=google_maps` | Scrape only |
| POST | `/scrape/process` | Score + outreach all new leads |
| POST | `/scrape/run?query=...&source=all` | **Full pipeline** |
| POST | `/leads/` | Add single lead manually |
| GET | `/leads/` | List all leads |
| GET | `/leads/stats` | Dashboard stats |
| GET | `/leads/{id}` | Get lead by ID |
| POST | `/leads/{id}/score` | Re-score a lead |

## Free API Keys

| Service | Purpose | Link |
|---------|---------|------|
| Gemini | AI scoring & message writing | https://aistudio.google.com/app/apikey |
| Tavily | Website enrichment | https://tavily.com |
| Apollo | B2B contact enrichment | https://app.apollo.io/#/settings/integrations/api |
| Apify | Google Maps scraping | https://apify.com |
| SendGrid | Email outreach | https://sendgrid.com (100/day free) |
