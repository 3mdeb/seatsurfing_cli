# 🪑 SeatSurfing Auto-Booking Script

Automatically reserve your preferred desk via the SeatSurfing API, either for a single day or the whole workweek.

## 🚀 Features

* Log in to your organization’s SeatSurfing instance.
* Check if a desk is available for a specific time.
* Reserve the desk automatically.
* Optionally reserve for **the full workweek** (Mon–Fri).
* Optionally **override the date** to book a specific day.
* All credentials and sensitive info stored in a local config file.

## 📦 Requirements

* Python 3.7+
* `requests` module (install via `pip install requests`)

## 🛠️ Setup

1. Clone this repo or copy the script locally.
2. Create a config file at `~/.config/seatsurfing/config.json`.

### Example `config.json`:

```json
{
  "BASE_URL": "http://your.seatsurfing.app",
  "EMAIL": "your.email@domain.com",
  "PASSWORD": "your_password",
  "ORG_ID": "your-org-id-here",
  "LOCATION_ID": "your-location-id-here"
}
```

> 🔒 **Keep this file secret!** Do **not** commit it to Git.

### Config file location

The config is looked up in this order (first match wins):

1. `--config <path>`
2. `$XDG_CONFIG_HOME/seatsurfing/config.json` (if `XDG_CONFIG_HOME` is set).
3. `~/.config/seatsurfing/config.json` (the default).
4. `.seatsurfing_config.json` next to the script (legacy fallback).

## 🧑‍💻 Usage

### Basic: Book a desk today

```bash
python seatsurf.py "Desk 7" "16:00-18:00"
```

This will:

* Check availability for "Desk 7" today between 16:00 and 18:00 (local time).
* Book it if available.

### Book a desk for a specific day

```bash
python seatsurf.py "Desk 7" "16:00-18:00" --day 18.07
```

This will:

* Attempt to reserve "Desk 7" for July 18th between 16:00 and 18:00.
* Accepts:
- `DD.MM` or `D.M` (e.g., `9.7`, `18.07`)
- `DD.MM.YYYY` or `D.M.YYYY` (e.g., `9.7.2025`, `01.01.2026`)

If the year is **not specified**:
- The script assumes the current year.
- But if that date has already passed this year, it automatically rolls over to the **next year**.

### Full Week Booking (Mon–Fri)

```bash
python seatsurf.py "Desk 7" "16:00-18:00" --week
```

This will:

* Attempt to book "Desk 7" for each weekday (Mon–Fri) **starting today** between 16:00 and 18:00.
* Continue even if some days are unavailable.

### Full Week Booking starting from a specific day

```bash
python seatsurf.py "Desk 7" "16:00-18:00" --week --day 18.07
```

This will:

* Attempt to book "Desk 7" for each weekday starting from **July 18th**.
* Handy for planning future weeks or mid-week starts.

## ⚠️ Notes

* Desk names must match **exactly** as listed in the SeatSurfing UI (e.g. `"Desk 7"`).
* Time format must be `HH:MM-HH:MM` in **24-hour format**.
* All times are assumed to be in **your local time**, but will be converted to UTC with `"Z"` suffix.
* The `--day` flag does not support full dates like `18.07.2025` (yet).

## 🧩 Future Ideas

* List all available desks (`--list`)
* Auto-pick any available desk
* Configurable subject line
* Timezone handling
* Support for full dates with year

## 🛡 License

MIT License. Use responsibly and don’t overload shared booking systems.

