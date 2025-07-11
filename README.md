# Aggression Analyzer Project

Aggression Analyzer is an all-in-one tool for collecting posts from X (formerly Twitter) and analyzing their level of aggression.  Posts are scraped with **ntscraper**, evaluated by OpenAI's moderation and chat models, and displayed in a desktop GUI built with **customtkinter**.

## Prerequisites

- **Python 3.10+** is recommended. ntscraper may not work correctly on older versions.
- An **OpenAI API key** is required. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
- Network access is needed to scrape X and to call the OpenAI API.

## Setup

Install the dependencies and create an environment file:

```bash
pip install -r requirements.txt
cp aggression_analyzer/.env.example .env
# edit .env and set OPENAI_API_KEY
```

## Usage

Run the GUI application:

```bash
python aggression_analyzer/main.py
```

In a headless environment you can use [`xvfb-run`](https://manpages.ubuntu.com/manpages/xenial/man1/xvfb-run.1.html):

```bash
xvfb-run -a python aggression_analyzer/main.py
```

Enter a Twitter user ID and the number of posts to fetch. The application will scrape the posts, analyze them, and allow you to save the results to an Excel file in the `output/` directory.

## Parallel Processing

Analysis requests are processed concurrently using `ThreadPoolExecutor`.
The maximum number of workers defaults to the constant
`MAX_CONCURRENT_WORKERS` defined in `config/settings.py`:

```python
MAX_CONCURRENT_WORKERS = 8
```

You can adjust this value to match your hardware resources and the
rate limits of the OpenAI API. Increasing it speeds up large batch
analysis at the cost of more simultaneous API calls.

Scraping is performed serially to avoid rate limiting. The delay between
requests can be adjusted with `SCRAPE_DELAY_SECONDS` in
`config/settings.py`.

Aggression score weights used to compute the final `total_aggression`
value can also be tuned.  Edit the `WEIGHTS` dictionary in
`config/settings.py` to change how each moderation category contributes
to the overall score.

## Archiving Selected Posts

After analysis, results are listed with checkboxes and are color coded
by aggression score (yellow for scores 4–6 and red for 7+).  Use the
slider above the list to choose the minimum score that should be
automatically selected.  Press the **Archive Selected Posts** button to
create Wayback Machine snapshots in a background thread.  The archive
URLs are stored alongside the posts when you save the Excel report.

## Running Tests

Basic functionality is covered by unit tests in the `tests/` directory. After installing the requirements, run:

```bash
pytest -q
```

All tests should pass.

## Project Structure

- `aggression_analyzer/main.py` – Loads environment variables and launches the GUI.
- `aggression_analyzer/gui/app.py` – `ModerationApp` class with the desktop interface.
- `aggression_analyzer/modules/scraper.py` – `Scraper` class for collecting posts.
- `aggression_analyzer/modules/analyzer.py` – `Analyzer` class for moderation and scoring.
- `aggression_analyzer/config/settings.py` – Configuration constants and aggression analysis prompt template.
- `aggression_analyzer/output/` – Default directory for generated Excel reports.


## Documentation

For Japanese instructions, see [docs/manual_ja.md](docs/manual_ja.md).

