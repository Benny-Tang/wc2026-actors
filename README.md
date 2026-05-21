# ⚽ WC2026 Actor Suite — Apify Store Portfolio

> **World Cup 2026 football data scrapers + AI prediction engine**
> Built for the Chinese-speaking Asia-Pacific betting & fantasy market.
> Passive income via Apify Store — earns while you sleep.

---

## 📦 Actor Portfolio

| Actor | Description | Status |
|---|---|---|
| `wc2026-fixtures` | All 104 matches — groups, schedules, venues, kickoff times | ✅ Ready |
| `wc2026-predictor` | AI-powered match predictions with Asian Handicap picks | ✅ Ready |

---

## 🏗️ Architecture

```
GitHub (this repo)
    ├── actors/wc2026-fixtures/     → deploys to Apify Store
    ├── actors/wc2026-predictor/    → deploys to Apify Store
    ├── prediction-model/           → deploys to HuggingFace Spaces
    └── notebooks/                  → Google Colab test notebooks
```

## 🚀 Quick Deploy to Apify

1. Fork this repo
2. Go to [Apify Console](https://console.apify.com) → Create Actor → Link GitHub repo
3. Set webhook: `Settings → GitHub → Auto-build on push`
4. Done — every `git push` auto-deploys

## 🎯 Target Market

Chinese-speaking AP: Mainland China, Hong Kong, Malaysia, Singapore, Taiwan
Primary buyers: betting affiliates, tipster platforms, fantasy apps, sports media

## 💰 Pricing Model (Pay Per Event)

- Fixtures data: $0.002 per fixture record
- Predictions: $0.01 per match prediction
- Estimated revenue at scale: $2,000–$6,000/month passive

---

*Built with ❤️ using Apify SDK + Claude API*
