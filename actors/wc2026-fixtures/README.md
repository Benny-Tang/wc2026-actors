# ⚽ FIFA World Cup 2026 — Fixture & Group Scraper

> **世界杯2026赛程抓取器** | 抓取全部104场赛程、分组数据、场馆信息

Scrape all **104 FIFA World Cup 2026 fixtures** across 12 groups and 48 teams.
Returns structured JSON — ready for betting platforms, fantasy apps, and sports media.

---

## 📊 What You Get

Each fixture record contains:

| Field | Description |
|---|---|
| `match_id` | Official FIFA match number |
| `group` | Group A–L or knockout round |
| `date` | Match date (YYYY-MM-DD) |
| `kickoff_local` | Local kickoff time |
| `timezone` | Venue timezone (EDT/CDT/PDT) |
| `home_team` / `away_team` | Team names (English or Chinese) |
| `venue` | Stadium name |
| `city` | Host city |
| `home_score` / `away_score` | Result (when available) |
| `status` | `scheduled` / `live` / `finished` |

---

## 🔧 Input Options

| Option | Type | Default | Description |
|---|---|---|---|
| `filter_group` | string | `""` | Filter by group (A–L) or round |
| `filter_team` | string | `""` | Filter by team name |
| `include_results` | boolean | `true` | Include scores |
| `language` | string | `"en"` | `en` / `zh-CN` / `zh-TW` |

---

## 📦 Example Output

```json
{
  "match_id": 7,
  "group": "C",
  "date": "2026-06-13",
  "kickoff_local": "18:00",
  "timezone": "EDT",
  "venue": "MetLife Stadium",
  "city": "New York/New Jersey",
  "home_team": "Brazil",
  "away_team": "Morocco",
  "status": "scheduled",
  "home_score": null,
  "away_score": null,
  "result": null
}
```

---

## 🌏 All 12 Groups (48 Teams)

| Group | Teams |
|---|---|
| A | Mexico, South Korea, South Africa, Czechia |
| B | Canada, Switzerland, Qatar, Bosnia-Herzegovina |
| C | Brazil, Morocco, Haiti, Scotland |
| D | United States, Paraguay, Australia, Türkiye |
| E | Germany, Curaçao, Ivory Coast, Ecuador |
| F | Netherlands, Japan, Sweden, Tunisia |
| G | Belgium, Egypt, Iran, New Zealand |
| H | Spain, Cape Verde, Saudi Arabia, Uruguay |
| I | France, Senegal, Iraq, Norway |
| J | Argentina, Algeria, Austria, Jordan |
| K | Portugal, DR Congo, Uzbekistan, Colombia |
| L | England, Croatia, Ghana, Panama |

---

## 🎯 Who Uses This Actor

- **Betting affiliate websites** — match preview content
- **Tipster platforms** — fixture data for picks
- **Fantasy football apps** — group stage data
- **Sports media** — WeChat/Weibo content automation
- **AI/RAG pipelines** — structured input for LLM match previews
- **n8n / Make / Zapier** — automated matchday workflows

---

## 🔗 Pair With

- **WC2026 Match Predictor** — AI-powered win probabilities + Asian Handicap picks
- **WC2026 Asian Handicap Odds Tracker** — coming soon

---

*Data source: FIFA official / Wikipedia public structured data*
*Updated: daily during tournament | Tournament: June 11 – July 19, 2026*

---

**中文说明** | 本Actor抓取2026年FIFA世界杯全部104场赛程数据，支持按分组或球队筛选，
输出结构化JSON数据，支持简体中文/繁体中文/英文输出。适合博彩平台、竞彩用户、幻想足球应用和体育媒体使用。
