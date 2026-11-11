import os
import signal
import asyncio
from typing import Optional
from telethon import TelegramClient

from src.services.keyword_service import (
    load_keywords,
    save_keywords,
    add_keyword_group,
    delete_keyword_group
)
from src.services.stats_service import (
    fetch_price_history,
    calculate_statistics,
    format_stats_report,
    parse_time_scope
)
from src.services.chart_service import generate_pricing_chart
from src.utils import send_telegram_photo, send_telegram_message


def run_stats_query_sync(
    client: TelegramClient,
    loop: asyncio.AbstractEventLoop,
    keyword: str,
    scope: str
):
    """Executes the async stats fetch from the synchronous console thread."""
    coro = fetch_price_history(client, keyword, scope=scope)
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    records, scope_label = future.result(timeout=60)
    return records, scope_label


def handle_console_stats(client: Optional[TelegramClient], loop: Optional[asyncio.AbstractEventLoop]):
    if not client or not loop:
        print("[ERROR] Telegram client is not running yet. Please wait a moment.")
        return

    current_keywords = load_keywords()
    print("\n--- Price Statistics & Chart Report ---")
    print("Monitored keywords:")
    for idx, group in enumerate(current_keywords):
        print(f"  [{idx}] {' '.join(group)}")
    
    choice = input("Enter keyword (or number from list above): ").strip()
    if not choice:
        return

    if choice.isdigit() and 0 <= int(choice) < len(current_keywords):
        selected_keyword = " ".join(current_keywords[int(choice)])
    else:
        selected_keyword = choice

    scope = input("Enter time scope (week / month / ever) [default: month]: ").strip()
    if not scope:
        scope = "month"

    print(f"\nSearching Telegram messages for \"{selected_keyword}\" ({scope})... Please wait...")
    try:
        records, scope_label = run_stats_query_sync(client, loop, selected_keyword, scope)
    except Exception as e:
        print(f"[ERROR] Failed to query Telegram: {e}")
        return

    if not records:
        print(f"No price records found for \"{selected_keyword}\" within {scope_label.lower()}.")
        return

    stats = calculate_statistics(records)
    report_text = format_stats_report(stats, selected_keyword, scope_label)
    print("\n" + "=" * 50)
    print(report_text)
    print("=" * 50)

    # Generate chart
    os.makedirs("reports", exist_ok=True)
    clean_name = "".join(c if c.isalnum() else "_" for c in selected_keyword).strip("_")
    chart_filename = f"reports/chart_{clean_name}_{scope}.png"
    
    try:
        chart_bytes = generate_pricing_chart(
            keyword=selected_keyword,
            scope_label=scope_label,
            records=records,
            stats=stats,
            save_path=chart_filename
        )
        print(f"[SUCCESS] Chart saved to: {os.path.abspath(chart_filename)}")
        
        send_to_tg = input("Send this report and chart to your Telegram chat? [y/N]: ").strip().lower()
        if send_to_tg in ("y", "yes", "s", "sim"):
            print("Sending to Telegram...")
            sent = send_telegram_photo(caption=report_text, photo=chart_bytes)
            if sent:
                print("Sent to Telegram successfully!")
            else:
                print("[ERROR] Could not send to Telegram.")
    except Exception as e:
        print(f"[ERROR] Failed to generate chart: {e}")


def keyword_console_manager(client: Optional[TelegramClient] = None, loop: Optional[asyncio.AbstractEventLoop] = None):
    while True:
        current_keywords = load_keywords()
        print("\n" + "-" * 35)
        print("Telegram Monitor Menu:")
        print("1. Add keyword group")
        print("2. Delete keyword group")
        print("3. List keyword groups")
        print("4. Query price statistics & chart report")
        print("5. Exit")
        cmd = input("Select option [1-5]: ").strip()
        
        if cmd == '1':
            group = input('Enter keyword group (comma separated): ').strip()
            group_list = [w.strip() for w in group.split(',') if w.strip()]
            if group_list:
                add_keyword_group(group_list)
                print(f"Added: {group_list} (saved to keywords.json)")
        elif cmd == '2':
            for idx, group in enumerate(current_keywords):
                print(f"{idx}: {group}")
            idx = input('Enter index to delete: ').strip()
            if idx.isdigit() and 0 <= int(idx) < len(current_keywords):
                removed = current_keywords[int(idx)]
                delete_keyword_group(int(idx))
                print(f"Removed: {removed} (saved to keywords.json)")
            else:
                print("Invalid index.")
        elif cmd == '3':
            print("\nCurrent Monitored Keywords:")
            for idx, group in enumerate(current_keywords):
                print(f"{idx}: {group}")
        elif cmd == '4':
            handle_console_stats(client, loop)
        elif cmd == '5':
            print('Exiting keyword manager and terminating bot.')
            os.kill(os.getpid(), signal.SIGINT)
            break
        else:
            print("Unknown option. Please select 1, 2, 3, 4, or 5.")
