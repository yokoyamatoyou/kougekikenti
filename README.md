# Aggression Analyzer Project

This project aims to provide an all-in-one tool for collecting and analyzing social media posts for aggressive content. It combines Twitter scraping using **snscrape**, OpenAI's moderation and language models, and a desktop GUI built with **customtkinter**.

## Prerequisites

- **Python 3.10+** is recommended. snscrape may not work correctly on some Python versions.
- An **OpenAI API key** is required to run the aggression analysis. Copy `.env.example` to `.env` and place your API key in `OPENAI_API_KEY`.
- Ensure network access to scrape X (formerly Twitter). Scraping may fail if the account is private or network requests are blocked.

## Setup

Install dependencies and set up environment variables:

```bash
pip install -r aggression_analyzer/requirements.txt
cp aggression_analyzer/.env.example aggression_analyzer/.env
# edit aggression_analyzer/.env and set OPENAI_API_KEY
```

## Usage

Run the GUI application:

```bash
python aggression_analyzer/main.py
```

The interface allows you to enter a Twitter user ID and the number of posts to fetch. The tool scrapes the posts, sends them to OpenAI for moderation and aggression scoring, and lets you save the results as an Excel file.

## Project Structure

- `aggression_analyzer/main.py` – Entry point loading environment variables and launching the GUI.
- `aggression_analyzer/gui/app.py` – `ModerationApp` class implementing the desktop interface.
- `aggression_analyzer/modules/scraper.py` – `Scraper` class using snscrape to collect posts.
- `aggression_analyzer/modules/analyzer.py` – `Analyzer` class calling OpenAI API for moderation and scoring.
- `aggression_analyzer/config/settings.py` – Configuration constants and aggression analysis prompt.
- `aggression_analyzer/output/` – Default directory for generated Excel reports.

