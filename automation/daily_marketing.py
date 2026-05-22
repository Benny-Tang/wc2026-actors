"""
WC2026 Daily Marketing Automation
===================================
Runs daily via Google Colab (free)
Posts predictions to Telegram + Twitter automatically
Sends daily report summary

Setup:
1. Add your API keys in the CONFIG section
2. Run this notebook daily (or schedule via Colab)
3. Fully autonomous — zero manual work needed
"""

import requests
import json
import datetime
import time
import os

# ══════════════════════════════════════════════════════════════
# CONFIG — Fill in your keys once, never touch again
# ══════════════════════════════════════════════════════════════
CONFIG = {
    # Apify
    "APIFY_TOKEN":          os.getenv("APIFY_TOKEN", "YOUR_APIFY_TOKEN"),
    "FIXTURE_ACTOR_ID":     "JpFxNZWI9ivm5f2D3",   # wc2026-fixture
    "PREDICTOR_ACTOR_ID":   "PdQyJIhYBPRwsWvYm",   # wc2026-predictor

    # Telegram
    "TELEGRAM_BOT_TOKEN":   os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN"),
    "TELEGRAM_CHANNEL_ID":  os.getenv("TELEGRAM_CHANNEL_ID", "@wc2026data"),

    # Twitter (optional)
    "TWITTER_API_KEY":      os.getenv("TWITTER_API_KEY", ""),
    "TWITTER_API_SECRET":   os.getenv("TWITTER_API_SECRET", ""),
    "TWITTER_ACCESS_TOKEN": os.getenv("TWITTER_ACCESS_TOKEN", ""),
    "TWITTER_ACCESS_SECRET":os.getenv("TWITTER_ACCESS_SECRET", ""),

    # Report email (optional)
    "REPORT_EMAIL":         os.getenv("REPORT_EMAIL", ""),
}

# ══════════════════════════════════════════════════════════════
# APIFY — Get today's fixtures and predictions
# ══════════════════════════════════════════════════════════════

def run_apify_actor(actor_id: str, input_data: dict) -> dict:
    """Run an Apify Actor and return results."""
    token = CONFIG["APIFY_TOKEN"]
    base  = "https://api.apify.com/v2"

    # Start run
    r = requests.post(
        f"{base}/acts/{actor_id}/runs",
        headers={"Authorization": f"Bearer {token}"},
        json={"input": input_data}
    )
    run = r.json().get("data", {})
    run_id = run.get("id")
    print(f"  Actor started — run ID: {run_id}")

    # Wait for completion
    for _ in range(30):
        time.sleep(3)
        status_r = requests.get(
            f"{base}/actor-runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        status = status_r.json().get("data", {}).get("status")
        if status == "SUCCEEDED":
            break
        elif status in ("FAILED", "ABORTED"):
            print(f"  ❌ Actor failed: {status}")
            return {}

    # Get results
    dataset_id = status_r.json()["data"]["defaultDatasetId"]
    results_r  = requests.get(
        f"{base}/datasets/{dataset_id}/items",
        headers={"Authorization": f"Bearer {token}"}
    )
    return results_r.json()

def get_todays_fixtures() -> list:
    """Get fixtures for today and next 2 days."""
    print("📅 Fetching fixtures...")
    results = run_apify_actor(
        CONFIG["FIXTURE_ACTOR_ID"],
        {"filter_group": "", "filter_team": "",
         "include_results": True, "language": "en"}
    )
    today = datetime.date.today()
    upcoming = []
    for f in results:
        try:
            match_date = datetime.date.fromisoformat(f.get("date",""))
            days_diff  = (match_date - today).days
            if 0 <= days_diff <= 2:
                upcoming.append(f)
        except:
            continue
    print(f"  Found {len(upcoming)} upcoming fixtures")
    return upcoming

def get_prediction(home: str, away: str, context: str = "group_stage") -> dict:
    """Get AI prediction for a specific match."""
    print(f"🤖 Getting prediction: {home} vs {away}...")
    results = run_apify_actor(
        CONFIG["PREDICTOR_ACTOR_ID"],
        {"home_team": home, "away_team": away,
         "match_context": context, "language": "en",
         "include_reasoning": False, "anthropic_api_key": ""}
    )
    return results[0] if results else {}

# ══════════════════════════════════════════════════════════════
# CONTENT — Format posts for each platform
# ══════════════════════════════════════════════════════════════

def format_telegram_chinese(fixture: dict, pred: dict) -> str:
    """Format Chinese Telegram post."""
    today    = datetime.date.today()
    match_dt = datetime.date.fromisoformat(fixture.get("date",""))
    days_away = (match_dt - today).days
    day_label = "今天" if days_away == 0 else f"{days_away}天后"

    home = fixture.get("home_team","")
    away = fixture.get("away_team","")
    grp  = fixture.get("group","")
    city = fixture.get("city","")
    kick = fixture.get("kickoff_local","")
    tz   = fixture.get("timezone","")

    hw   = pred.get("home_win_pct", 0)
    dr   = pred.get("draw_pct", 0)
    aw   = pred.get("away_win_pct", 0)
    ahp  = pred.get("asian_handicap_pick","")
    ahl  = pred.get("asian_handicap_line", 0)
    conf = pred.get("confidence", 0)
    winner = pred.get("predicted_winner","")

    return f"""
⚽ 世界杯2026 | {day_label}比赛预测

🏟️ 小组{grp} | {city}
⏰ {kick} {tz}

{home} vs {away}

📊 AI概率分析：
🏠 {home} 胜：{hw}%
🤝 平局：{dr}%
✈️ {away} 胜：{aw}%

🎯 亚盘推荐：{ahp} ({ahl:+.1f})
💪 信心指数：{conf}/10
🏆 预测结果：{winner}

⚠️ 仅供参考，不构成投注建议

📅 赛程数据：apify.com/kindly_bolt/wc2026-actors
🤖 AI预测：apify.com/kindly_bolt/wc2026-actors-1

#世界杯2026 #足球预测 #亚盘 #WC2026
""".strip()

def format_telegram_english(fixture: dict, pred: dict) -> str:
    """Format English Telegram/Twitter post."""
    today    = datetime.date.today()
    match_dt = datetime.date.fromisoformat(fixture.get("date",""))
    days_away = (match_dt - today).days
    day_label = "TODAY" if days_away == 0 else f"in {days_away} days"

    home = fixture.get("home_team","")
    away = fixture.get("away_team","")
    grp  = fixture.get("group","")
    city = fixture.get("city","")
    kick = fixture.get("kickoff_local","")
    tz   = fixture.get("timezone","")

    hw   = pred.get("home_win_pct", 0)
    dr   = pred.get("draw_pct", 0)
    aw   = pred.get("away_win_pct", 0)
    ahp  = pred.get("asian_handicap_pick","")
    ahl  = pred.get("asian_handicap_line", 0)
    conf = pred.get("confidence", 0)
    winner = pred.get("predicted_winner","")

    return f"""
⚽ WC2026 Match Prediction — {day_label}!

Group {grp} | {city} | {kick} {tz}
{home} vs {away}

📊 AI Probabilities:
🏠 {home}: {hw}%
🤝 Draw: {dr}%
✈️ {away}: {aw}%

🎯 Asian Handicap: {ahp} ({ahl:+.1f})
💪 Confidence: {conf}/10
🏆 Prediction: {winner}

Data: apify.com/kindly_bolt/wc2026-actors
AI: apify.com/kindly_bolt/wc2026-actors-1

#WC2026 #WorldCup2026 #football #AsianHandicap
""".strip()

def format_twitter(fixture: dict, pred: dict) -> str:
    """Format Twitter post — max 280 chars."""
    home   = fixture.get("home_team","")
    away   = fixture.get("away_team","")
    hw     = pred.get("home_win_pct", 0)
    dr     = pred.get("draw_pct", 0)
    aw     = pred.get("away_win_pct", 0)
    ahp    = pred.get("asian_handicap_pick","")
    ahl    = pred.get("asian_handicap_line", 0)
    conf   = pred.get("confidence", 0)

    post = (
        f"⚽ #WC2026 Prediction\n"
        f"{home} vs {away}\n"
        f"🏠{hw}% 🤝{dr}% ✈️{aw}%\n"
        f"🎯AH: {ahp}({ahl:+.1f}) 💪{conf}/10\n"
        f"apify.com/kindly_bolt/wc2026-actors-1\n"
        f"#WorldCup2026 #AsianHandicap #世界杯2026"
    )
    return post[:280]

# ══════════════════════════════════════════════════════════════
# POST — Send to platforms
# ══════════════════════════════════════════════════════════════

def post_telegram(message: str) -> bool:
    """Post message to Telegram channel."""
    token   = CONFIG["TELEGRAM_BOT_TOKEN"]
    channel = CONFIG["TELEGRAM_CHANNEL_ID"]

    if token == "YOUR_BOT_TOKEN":
        print("  ⚠️ Telegram not configured — printing message only")
        print(f"\n{'='*50}\nTELEGRAM MESSAGE:\n{message}\n{'='*50}\n")
        return False

    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": channel, "text": message, "parse_mode": "HTML"}
    )
    if r.status_code == 200:
        print("  ✅ Telegram posted!")
        return True
    else:
        print(f"  ❌ Telegram failed: {r.text}")
        return False

def post_twitter(message: str) -> bool:
    """Post tweet via Twitter API v2."""
    api_key    = CONFIG["TWITTER_API_KEY"]
    api_secret = CONFIG["TWITTER_API_SECRET"]
    acc_token  = CONFIG["TWITTER_ACCESS_TOKEN"]
    acc_secret = CONFIG["TWITTER_ACCESS_SECRET"]

    if not api_key:
        print("  ⚠️ Twitter not configured — skipping")
        print(f"\nTWITTER POST:\n{message}\n")
        return False

    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=acc_token,
            access_token_secret=acc_secret
        )
        client.create_tweet(text=message)
        print("  ✅ Twitter posted!")
        return True
    except Exception as e:
        print(f"  ❌ Twitter failed: {e}")
        return False

# ══════════════════════════════════════════════════════════════
# DAILY REPORT
# ══════════════════════════════════════════════════════════════

def generate_daily_report(results: list) -> str:
    """Generate daily marketing report."""
    today     = datetime.date.today()
    days_left = (datetime.date(2026, 6, 11) - today).days

    report = f"""
╔══════════════════════════════════════════╗
   📊 WC2026 DAILY MARKETING REPORT
   {today.strftime('%A, %B %d, %Y')}
   ⏰ {days_left} days to World Cup kickoff
╚══════════════════════════════════════════╝

POSTS SENT TODAY:
"""
    for i, r in enumerate(results, 1):
        report += f"""
Match {i}: {r.get('home')} vs {r.get('away')}
  ✅ Telegram (Chinese): {'✅' if r.get('tg_cn') else '❌'}
  ✅ Telegram (English): {'✅' if r.get('tg_en') else '❌'}
  ✅ Twitter:            {'✅' if r.get('tw') else '❌'}
"""

    report += f"""
ACTOR URLS:
  📅 Fixtures:  apify.com/kindly_bolt/wc2026-actors
  🤖 Predictor: apify.com/kindly_bolt/wc2026-actors-1

NEXT RUN: Tomorrow {(today + datetime.timedelta(days=1)).strftime('%B %d')}
══════════════════════════════════════════
"""
    return report

# ══════════════════════════════════════════════════════════════
# MAIN — Run everything
# ══════════════════════════════════════════════════════════════

def run_daily_marketing():
    """Main function — runs the full daily marketing cycle."""
    print("\n🚀 WC2026 Daily Marketing Automation Starting...")
    print(f"📅 Date: {datetime.date.today()}")
    print(f"⏰ Time: {datetime.datetime.now().strftime('%H:%M')}")
    print("="*50)

    results = []

    # Get upcoming fixtures
    fixtures = get_todays_fixtures()

    if not fixtures:
        print("⚠️ No fixtures today/tomorrow — posting general promo")
        # Post general promo instead
        promo = """
⚽ 世界杯2026倒计时！

免费获取全部赛程数据+AI预测：

📅 赛程抓取器：
apify.com/kindly_bolt/wc2026-actors

🤖 AI预测+亚盘推荐：
apify.com/kindly_bolt/wc2026-actors-1

支持简体中文/繁体中文/英文 🌏
#世界杯2026 #WC2026 #足球预测
        """.strip()
        post_telegram(promo)
        return

    # Process max 3 matches per day (avoid spam)
    for fixture in fixtures[:3]:
        home = fixture.get("home_team","")
        away = fixture.get("away_team","")

        print(f"\n📌 Processing: {home} vs {away}")

        # Get prediction
        pred = get_prediction(home, away)

        if not pred:
            print(f"  ⚠️ No prediction available — skipping")
            continue

        # Format content
        tg_cn = format_telegram_chinese(fixture, pred)
        tg_en = format_telegram_english(fixture, pred)
        tw    = format_twitter(fixture, pred)

        # Post to platforms
        print(f"\n📤 Posting: {home} vs {away}")
        tg_cn_ok = post_telegram(tg_cn)
        time.sleep(3)  # Avoid rate limits
        tg_en_ok = post_telegram(tg_en)
        time.sleep(3)
        tw_ok    = post_twitter(tw)

        results.append({
            "home":  home,
            "away":  away,
            "tg_cn": tg_cn_ok,
            "tg_en": tg_en_ok,
            "tw":    tw_ok,
        })

        time.sleep(5)  # Gap between matches

    # Generate and print daily report
    report = generate_daily_report(results)
    print(report)
    return report

# ══════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_daily_marketing()
