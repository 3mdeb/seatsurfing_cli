#!/usr/bin/python3

import json
import requests
import datetime
from urllib.parse import urlencode
import os
import sys
import argparse

def default_config_path():
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config")
    return os.path.join(xdg, "seatsurfing", "config.json")

def config_candidates(cli_path=None):
    candidates = [cli_path] if cli_path else []
    candidates.append(default_config_path())
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(script_dir, ".seatsurfing_config.json"))
    return candidates

def load_config(cli_path=None):
    candidates = config_candidates(cli_path)
    for path in candidates:
        if path and os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    print("❌ Config file not found. Searched:")
    for c in candidates:
        if c:
            print(f"  - {c}")
    print("Set one up or pass --config <path>.")
    sys.exit(1)

def check_api_alive(base_url):
    test_endpoints = ["/auth/ping", "/location", "/swagger", "/"]
    print("🔍 Probing API endpoints...")
    for path in test_endpoints:
        try:
            resp = requests.get(base_url + path, timeout=5)
            print(f"GET {path} → {resp.status_code}")
            if resp.status_code == 200:
                print("✅ API appears responsive.")
                return True
        except Exception as e:
            print(f"GET {path} → ❌ {e}")
    print("❌ API seems unreachable.")
    return False

def login(base_url, email, password, org_id):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": base_url,
        "Referer": f"{base_url}/ui/login/",
        "User-Agent": "Mozilla/5.0"
    }

    payload = {
        "email": email,
        "password": password,
        "organizationId": org_id,
        "longLived": False
    }

    resp = requests.post(f"{base_url}/auth/login", headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    print(data)
    access_token = data["accessToken"]

    print("✅ Logged in! Access token:", access_token[:20], "…")
    return access_token

def check_availability_and_get_id(base_url, location_id, desk_label, enter, leave, access_token):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}",
        "Origin": base_url,
        "Referer": f"{base_url}/ui/search/",
        "User-Agent": "Mozilla/5.0"
    }

    params = {"enter": enter, "leave": leave}
    url = f"{base_url}/location/{location_id}/space/availability?{urlencode(params)}"
    resp = requests.get(url, headers=headers)
    print(f"🔍 Availability check for {enter[:10]} → {resp.status_code}")
    resp.raise_for_status()

    spaces = resp.json()

    for space in spaces:
        name = space.get("name") or ""
        if name.lower() == desk_label.lower() and space.get("available") and space.get("allowed", True):
            print(f"✅ '{desk_label}' is available on {enter[:10]}")
            return space["id"]

    print(f"❌ '{desk_label}' is NOT available on {enter[:10]}")
    return None

def make_reservation(base_url, desk_id, desk_label, enter, leave, access_token, subject="skibidooobi"):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}",
        "Origin": base_url,
        "Referer": f"{base_url}/ui/search/",
        "User-Agent": "Mozilla/5.0"
    }

    booking_payload = {
        "enter": enter,
        "leave": leave,
        "spaceId": desk_id,
        "subject": subject,
        "userEmail": ""
    }

    resp = requests.post(f"{base_url}/booking/", json=booking_payload, headers=headers)
    print(f"📡 Booking on {enter[:10]} status: {resp.status_code}")
    print("📨 Response:", resp.text)
    resp.raise_for_status()
    print(f"✅ Successfully booked '{desk_label}' on {enter[:10]} from {enter[-13:-8]} to {leave[-13:-8]}.")

def list_reservations(base_url, access_token):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    url = f"{base_url}/booking/"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    bookings = resp.json()

    if not bookings:
        print("📭 No current reservations found.")
        return

    print("📋 Your Reservations:")
    for b in bookings:
        enter = b["enter"]
        leave = b["leave"]
        space_name = b.get("space", {}).get("name", "Unknown")
        print(f"• {space_name}: {enter} → {leave}")

def parse_time_range(time_str, day):
    try:
        start_str, end_str = time_str.split("-")
        enter = f"{day.isoformat()}T{start_str}:00.000Z"
        leave = f"{day.isoformat()}T{end_str}:00.000Z"
        return enter, leave
    except ValueError:
        print("❌ Invalid time format. Use HH:MM-HH:MM (e.g. 16:00-18:00)")
        sys.exit(1)

def get_weekdays(start_day, count=5):
    weekdays = []
    current = start_day
    while len(weekdays) < count:
        if current.weekday() < 5:
            weekdays.append(current)
        current += datetime.timedelta(days=1)
    return weekdays

def parse_day_argument(day_str):
    try:
        parts = day_str.strip().split(".")
        if len(parts) not in [2, 3]:
            raise ValueError("Invalid number of components")

        day = int(parts[0])
        month = int(parts[1])
        today = datetime.date.today()

        if len(parts) == 3:
            year = int(parts[2])
        else:
            year = today.year
            try_date = datetime.date(year, month, day)
            if try_date < today:
                year += 1

        return datetime.date(year, month, day)

    except ValueError:
        print("❌ Invalid day format. Use DD.MM or DD.MM.YYYY (e.g., 01.01 or 01.01.2025)")
        sys.exit(1)

def handle_book_command(args, config):
    BASE_URL = config["BASE_URL"]
    EMAIL = config["EMAIL"]
    PASSWORD = config["PASSWORD"]
    ORG_ID = config["ORG_ID"]
    LOCATION_ID = config["LOCATION_ID"]

    if not check_api_alive(BASE_URL):
        sys.exit(1)

    access_token = login(BASE_URL, EMAIL, PASSWORD, ORG_ID)

    desk_label = args.desk_label
    time_range = args.time_range
    override_day = parse_day_argument(args.day) if args.day else None

    if args.week:
        start_day = override_day or datetime.date.today()
        days = get_weekdays(start_day)
        print(f"\n📅 Attempting to reserve '{desk_label}' for the full week starting {start_day.isoformat()}...\n")
        for day in days:
            enter, leave = parse_time_range(time_range, day)
            desk_id = check_availability_and_get_id(BASE_URL, LOCATION_ID, desk_label, enter, leave, access_token)
            if desk_id:
                try:
                    make_reservation(BASE_URL, desk_id, desk_label, enter, leave, access_token)
                except Exception as e:
                    print(f"❌ Booking failed on {day.isoformat()}: {e}")
            else:
                print(f"⚠️ Skipping {day.isoformat()} — desk not available.\n")
    else:
        day = override_day or datetime.date.today()
        enter, leave = parse_time_range(time_range, day)
        desk_id = check_availability_and_get_id(BASE_URL, LOCATION_ID, desk_label, enter, leave, access_token)
        if desk_id:
            make_reservation(BASE_URL, desk_id, desk_label, enter, leave, access_token)

def handle_list_command(config):
    BASE_URL = config["BASE_URL"]
    EMAIL = config["EMAIL"]
    PASSWORD = config["PASSWORD"]
    ORG_ID = config["ORG_ID"]

    if not check_api_alive(BASE_URL):
        sys.exit(1)

    access_token = login(BASE_URL, EMAIL, PASSWORD, ORG_ID)
    list_reservations(BASE_URL, access_token)

def main():
    parser = argparse.ArgumentParser(description="SeatSurfing CLI")
    parser.add_argument("--config", help="Path to the config file (overrides the default XDG location)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    book_parser = subparsers.add_parser("book", help="Book a desk")
    book_parser.add_argument("desk_label", help="Label of the desk to reserve (e.g. 'Desk 7')")
    book_parser.add_argument("time_range", help="Time range (e.g. '16:00-18:00')")
    book_parser.add_argument("--week", action="store_true", help="Reserve the desk for the full week (Mon–Fri)")
    book_parser.add_argument("--day", help="Specify the day (DD.MM or DD.MM.YYYY) to reserve instead of today")

    list_reservations_parser = subparsers.add_parser("list_reservations", help="List your current reservations")

    args = parser.parse_args()
    config = load_config(args.config)

    if args.command == "book":
        handle_book_command(args, config)
    elif args.command == "list_reservations":
        handle_list_command(config)

if __name__ == "__main__":
    main()
