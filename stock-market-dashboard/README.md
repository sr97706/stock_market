# Stock Dashboard Project

## Overview
This project is a simple stock market dashboard that fetches live stock data using the `yfinance` API. It includes:

- A **backend** REST API built with FastAPI that:
  - Serves a list of companies from a SQLite database.
  - Fetches historical stock data for a selected company from Yahoo Finance.
- A **frontend** built with plain HTML, CSS, and JavaScript that:
  - Displays the company list.
  - Shows historical stock data for the selected company.


## Setup and Run

### Backend

1. Navigate to the backend folder:

   ```bash
   cd backend
pip install -r requirements.txt
uvicorn app:app --reload 
# Frontend
cd frontend
python -m http.server 3000 --bind 127.0.0.1
