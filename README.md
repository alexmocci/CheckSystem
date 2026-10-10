# CheckSystem

**A lightweight system and service monitoring tool built with Python.**

SysWatch monitors local system resources and configured web services, stores historical data in SQLite, detects threshold violations and service status changes, and presents monitoring data through a Streamlit dashboard.

## Features

- **System monitoring:** CPU, memory and disk usage.
- **Service monitoring:** HTTP availability checks and response-time tracking.
- **Persistent storage:** SQLite database for metrics, checks and events.
- **Configurable thresholds:** CPU, memory and disk alerts.
- **Event tracking:** records service failures, recoveries, threshold alerts and recoveries.
- **Telegram notifications:** optional notifications for threshold events.
- **Interactive dashboard:** Streamlit interface for metrics and monitoring history.
- **Command-line history:** inspect historical metrics, statistics and events.
- **Automated tests:** pytest-based tests for core database and alert functionality.
- **Application logging:** console and rotating file logs.

## Tech stack

- Python
- SQLite
- psutil
- requests
- Streamlit
- pandas
- pytest

## Requirements

- Python 3.10 or newer
- pip
- Windows or Linux
- Internet access for remote service checks and optional Telegram notifications

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/alexmocci/CheckSystem.git
cd CheckSystem
```

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `config.example.json` to `config.json` and customize the service URLs, monitoring interval, disk path and thresholds.

## Configuration

Example:

```json
{
  "interval_seconds": 10,
  "disk_path": "C:\\",
  "services": [
    {
      "name": "Example Website",
      "url": "https://example.com"
    }
  ],
  "thresholds": {
    "cpu_percent": 85,
    "memory_percent": 90,
    "disk_percent": 90
  }
}
```

Use `/` as `disk_path` on Linux.

## Running SysWatch

Start the monitoring process:

```bash
python main.py
```

Start the dashboard in a separate terminal:

```bash
python -m streamlit run dashboard.py
```

Use the command-line history tools:

```bash
python history.py metrics --limit 20
python history.py stats --hours 24
python history.py services --hours 24
python history.py events --limit 20
python history.py thresholds --limit 20
```

## Optional Telegram notifications

Create a Telegram bot and configure the following environment variables in a local `.env` file:

```dotenv
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Never commit `.env` or publish your bot token.

## Tests

Run the test suite:

```bash
python -m pytest -v
```

## Project goals

SysWatch is a personal portfolio project focused on practical Python development, monitoring, persistence, automated testing and basic operational tooling.

## Future improvements

- Improved error handling and notification reliability
- Additional dashboard visualizations
- More extensive test coverage
- Packaging and deployment options
- Support for additional notification channels

## Author

**Alessandro Mocci**

GitHub: [@alexmocci](https://github.com/alexmocci/)