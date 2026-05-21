"""
WC2026 AI Match Predictor
=========================
Apify Actor — main.py

AI-powered match predictions for FIFA World Cup 2026.
Uses Elo ratings + recent form data + Claude AI reasoning.
Outputs: win/draw/loss %, Asian Handicap pick, confidence score.

Target: Chinese-speaking AP betting affiliates & tipster platforms.
"""

import json
import asyncio
import logging
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Team Elo Ratings (FIFA World Rankings proxy, May 2026) ────────────────────
# Source: EloRatings.net / FIFA Rankings — publicly available
ELO_RATINGS = {
    "Argentina":            2063,
    "France":               2050,
    "England":              2020,
    "Brazil":               2010,
    "Spain":                2008,
    "Portugal":             1990,
    "Belgium":              1985,
    "Netherlands":          1975,
    "Germany":              1965,
    "Uruguay":              1940,
    "Colombia":             1930,
    "Croatia":              1920,
    "Morocco":              1910,
    "Switzerland":          1905,
    "Japan":                1900,
    "Mexico":               1890,
    "United States":        1880,
    "South Korea":          1870,
    "Senegal":              1860,
    "Austria":              1850,
    "Ecuador":              1845,
    "Denmark":              1840,
    "Sweden":               1835,
    "Australia":            1820,
    "Iran":                 1815,
    "Türkiye":              1810,
    "Norway":               1800,
    "Scotland":             1795,
    "Ivory Coast":          1790,
    "Tunisia":              1780,
    "Algeria":              1775,
    "Egypt":                1770,
    "South Africa":         1760,
    "Canada":               1755,
    "Saudi Arabia":         1750,
    "Paraguay":             1745,
    "Ghana":                1740,
    "Bosnia and Herzegovina": 1735,
    "Qatar":                1720,
    "DR Congo":             1710,
    "Jordan":               1700,
    "Uzbekistan":           1695,
    "Panama":               1690,
    "Cape Verde":           1685,
    "Iraq":                 1680,
    "Haiti":                1660,
    "Czechia":              1850,
    "New Zealand":          1620,
    "Curacao":              1600,
}

# ── Recent form (last 5 competitive matches) — W=3, D=1, L=0 ─────────────────
RECENT_FORM = {
    "Argentina":   [3,3,3,1,3], "France": [3,3,1,3,3], "England": [3,3,3,1,3],
    "Brazil":      [3,1,3,3,1], "Spain":  [3,3,3,3,1], "Portugal": [3,3,3,1,3],
    "Germany":     [3,3,1,3,3], "Belgium": [3,1,3,3,3], "Netherlands": [3,3,3,1,3],
    "Morocco":     [3,1,3,3,3], "Japan":  [3,3,1,3,1], "Colombia": [3,3,3,1,3],
    "Uruguay":     [3,3,1,3,1], "Croatia": [1,3,3,1,3], "Switzerland": [3,3,1,1,3],
    "South Korea": [3,1,3,1,3], "Senegal": [3,3,1,3,1], "Mexico": [3,1,1,3,3],
    "United States":[3,3,1,3,3], "Austria":[3,3,3,1,1], "Ecuador":[3,1,3,3,1],
    "Sweden":      [3,3,1,3,1], "Australia":[1,3,3,1,3], "Iran":[3,3,1,1,3],
    "Türkiye":     [3,1,3,3,1], "Norway": [3,3,3,1,1], "Scotland":[1,3,1,3,3],
    "Ivory Coast": [3,3,1,1,3], "Tunisia":[1,3,3,1,1], "Algeria":[3,1,3,3,1],
    "Egypt":       [3,3,1,1,3], "South Africa":[1,3,3,1,3], "Canada":[3,3,1,3,1],
    "Saudi Arabia":[3,1,1,3,3], "Paraguay":[1,3,3,1,3], "Ghana":[3,1,3,1,3],
    "Bosnia and Herzegovina":[3,1,3,1,1], "Qatar":[1,1,3,3,1], "DR Congo":[3,3,1,1,1],
    "Jordan":      [1,3,1,3,1], "Uzbekistan":[3,1,3,1,3], "Panama":[1,3,1,1,3],
    "Cape Verde":  [3,3,1,1,3], "Iraq":[1,3,3,1,1], "Haiti":[1,1,3,1,3],
    "Czechia":     [3,1,3,3,1], "New Zealand":[1,1,3,1,1], "Curacao":[1,1,1,3,1],
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_elo(team: str) -> int:
    return ELO_RATINGS.get(team, 1700)

def get_form_score(team: str) -> float:
    """Weighted recent form 0-15, most recent match weighted highest."""
    form = RECENT_FORM.get(team, [1,1,1,1,1])
    weights = [0.10, 0.15, 0.20, 0.25, 0.30]  # most recent = highest weight
    return sum(f * w for f, w in zip(form, weights)) * (15 / 3)

def elo_win_probability(elo_a: int, elo_b: int) -> float:
    """Standard Elo expected score for team A vs team B."""
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

def calculate_probabilities(home: str, away: str) -> dict:
    """
    Calculate win/draw/loss probabilities using Elo + form adjustment.
    Returns percentages summing to 100.
    """
    elo_h = get_elo(home)
    elo_a = get_elo(away)
    form_h = get_form_score(home)
    form_a = get_form_score(away)

    # Base Elo probability
    base_win_h = elo_win_probability(elo_h, elo_a)

    # Form adjustment (max ±5% swing)
    form_diff = (form_h - form_a) / 15  # normalise to -1..1
    form_adj  = form_diff * 0.05

    adjusted_win_h = max(0.05, min(0.85, base_win_h + form_adj))

    # Draw probability: higher when teams are closer in strength
    elo_gap = abs(elo_h - elo_a)
    draw_base = max(0.18, 0.32 - (elo_gap / 2000))

    # Distribute remaining probability
    remaining  = 1 - draw_base
    win_h      = adjusted_win_h * remaining
    win_a      = (1 - adjusted_win_h) * remaining

    # Normalise to 100%
    total = win_h + draw_base + win_a
    return {
        "home_win_pct":  round((win_h / total) * 100, 1),
        "draw_pct":      round((draw_base / total) * 100, 1),
        "away_win_pct":  round((win_a / total) * 100, 1),
    }

def calculate_asian_handicap(home: str, away: str, probs: dict) -> dict:
    """
    Derive Asian Handicap recommendation from win probabilities.
    Common AH lines: 0, -0.5, -1, -1.5, +0.5, +1, +1.5
    """
    win_diff = probs["home_win_pct"] - probs["away_win_pct"]

    if win_diff > 30:
        line, pick, rationale = -1.5, home, "Strong favourite — lay -1.5 goals"
    elif win_diff > 18:
        line, pick, rationale = -1.0, home, "Clear favourite — lay -1 goal"
    elif win_diff > 8:
        line, pick, rationale = -0.5, home, "Slight edge — lay -0.5 goals"
    elif win_diff > -8:
        line, pick, rationale = 0.0,  "Draw", "Evenly matched — level ball"
    elif win_diff > -18:
        line, pick, rationale = 0.5,  away, "Away side slight edge — take +0.5"
    elif win_diff > -30:
        line, pick, rationale = 1.0,  away, "Away clear favourite — take +1"
    else:
        line, pick, rationale = 1.5,  away, "Away strong favourite — take +1.5"

    return {
        "ah_line":      line,
        "ah_pick":      pick,
        "ah_rationale": rationale,
    }

def confidence_score(elo_h: int, elo_a: int) -> int:
    """Confidence 1-10 based on Elo gap — bigger gap = more confident."""
    gap = abs(elo_h - elo_a)
    return min(10, max(1, round(gap / 50)))

def call_claude_api(home: str, away: str, probs: dict, ah: dict,
                    context: str, language: str, api_key: str) -> str:
    """
    Call Anthropic Claude API for richer match analysis text.
    Falls back to template if API key not provided.
    """
    if not api_key:
        return _template_analysis(home, away, probs, ah, language)

    lang_instruction = {
        "zh-CN": "请用简体中文回复。",
        "zh-TW": "請用繁體中文回覆。",
        "en":    "Reply in English.",
    }.get(language, "Reply in English.")

    prompt = f"""You are a professional football analyst specialising in World Cup predictions.

Match: {home} vs {away}
Tournament: FIFA World Cup 2026 — {context.replace('_', ' ').title()}

Statistical model output:
- {home} win probability: {probs['home_win_pct']}%
- Draw: {probs['draw_pct']}%
- {away} win: {probs['away_win_pct']}%
- Asian Handicap pick: {ah['ah_pick']} ({ah['ah_line']:+.1f})

Write a concise 3-paragraph match preview:
1. Team strengths and current form
2. Key tactical matchup and what to watch
3. Prediction summary with Asian Handicap recommendation

{lang_instruction}
Keep it factual, professional and useful for betting/fantasy decisions.
Respond ONLY with the analysis text, no headers or JSON."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 600,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]
    except Exception as e:
        log.warning(f"Claude API call failed: {e} — using template fallback")
        return _template_analysis(home, away, probs, ah, language)

def _template_analysis(home: str, away: str, probs: dict, ah: dict, language: str) -> str:
    """Template analysis when no API key is provided."""
    if language in ("zh-CN", "zh-TW"):
        return (
            f"根据Elo评分和近期状态分析，{home}在本场比赛中"
            f"{'占据优势' if probs['home_win_pct'] > probs['away_win_pct'] else '略处下风'}。"
            f"{home}获胜概率{probs['home_win_pct']}%，平局{probs['draw_pct']}%，"
            f"{away}获胜{probs['away_win_pct']}%。"
            f"亚盘推荐：{ah['ah_pick']} ({ah['ah_line']:+.1f})。{ah['ah_rationale']}。"
        )
    return (
        f"Based on Elo ratings and recent form, {home} "
        f"{'hold an advantage' if probs['home_win_pct'] > probs['away_win_pct'] else 'are slight underdogs'} "
        f"in this fixture. Win probabilities: {home} {probs['home_win_pct']}%, "
        f"Draw {probs['draw_pct']}%, {away} {probs['away_win_pct']}%. "
        f"Asian Handicap recommendation: {ah['ah_pick']} ({ah['ah_line']:+.1f}). "
        f"{ah['ah_rationale']}."
    )

# ── Main ───────────────────────────────────────────────────────────────────────

async def main():
    log.info("🤖 WC2026 AI Match Predictor starting...")

    try:
        from apify import Actor
        async with Actor:
            inp = await Actor.get_input() or {}

            home_team    = inp.get("home_team", "Brazil")
            away_team    = inp.get("away_team", "Morocco")
            context      = inp.get("match_context", "group_stage")
            language     = inp.get("language", "en")
            incl_reason  = inp.get("include_reasoning", True)
            api_key      = inp.get("anthropic_api_key", "")

            dataset = await Actor.open_dataset()
            result  = _predict(home_team, away_team, context, language, incl_reason, api_key)
            await dataset.push_data(result)
            log.info(f"✅ Prediction complete: {home_team} vs {away_team}")

    except ImportError:
        _run_local()

def _predict(home: str, away: str, context: str,
             language: str, incl_reason: bool, api_key: str) -> dict:
    probs = calculate_probabilities(home, away)
    ah    = calculate_asian_handicap(home, away, probs)
    conf  = confidence_score(get_elo(home), get_elo(away))

    record = {
        "home_team":       home,
        "away_team":       away,
        "match_context":   context,
        "home_win_pct":    probs["home_win_pct"],
        "draw_pct":        probs["draw_pct"],
        "away_win_pct":    probs["away_win_pct"],
        "predicted_winner": (
            home if probs["home_win_pct"] > probs["away_win_pct"] + 5
            else away if probs["away_win_pct"] > probs["home_win_pct"] + 5
            else "Draw"
        ),
        "asian_handicap_line": ah["ah_line"],
        "asian_handicap_pick": ah["ah_pick"],
        "ah_rationale":        ah["ah_rationale"],
        "confidence":          conf,
        "home_elo":            get_elo(home),
        "away_elo":            get_elo(away),
        "home_form_score":     round(get_form_score(home), 1),
        "away_form_score":     round(get_form_score(away), 1),
        "predicted_at":        datetime.utcnow().isoformat() + "Z",
        "model":               "Elo+Form v1.0 + Claude AI",
        "disclaimer":          "Predictions are probabilistic. Max ~55% accuracy is industry standard. Not financial advice.",
    }

    if incl_reason:
        record["ai_analysis"] = call_claude_api(
            home, away, probs, ah, context, language, api_key
        )

    return record

def _run_local():
    """Local / Colab test — runs a sample Brazil vs Morocco prediction."""
    print("=== WC2026 AI Predictor — Local Test Mode ===\n")
    test_matches = [
        ("Brazil",    "Morocco",   "group_stage"),
        ("England",   "Croatia",   "group_stage"),
        ("Argentina", "Algeria",   "group_stage"),
        ("France",    "Senegal",   "group_stage"),
        ("Germany",   "Curacao",   "group_stage"),
        ("Japan",     "Netherlands","group_stage"),
    ]
    for home, away, ctx in test_matches:
        result = _predict(home, away, ctx, "en", False, "")
        print(f"{'─'*55}")
        print(f"  {home} vs {away}")
        print(f"  Win%:  {result['home_win_pct']}% / {result['draw_pct']}% / {result['away_win_pct']}%")
        print(f"  AH:    {result['asian_handicap_pick']} ({result['asian_handicap_line']:+.1f})")
        print(f"  Pred:  {result['predicted_winner']}  |  Confidence: {result['confidence']}/10")
    print(f"{'─'*55}")
    print("\n✅ Local prediction test complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        _run_local()
