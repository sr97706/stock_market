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


# Stock Market Dashboard

## Short Note

For this project, I built a Stock Market Dashboard using a backend + frontend approach.

**Backend:**  
I used FastAPI in Python to create APIs that fetch stock data from `yfinance` (real-time and historical). The data is stored in a SQLite database (`stocks.db`) so the app still works if the API is unavailable. Features include:
- 52-week high/low prices
- Average trading volume
- AI-based price prediction using Linear Regression

**Frontend:**  
The frontend uses HTML, CSS, and JavaScript. It shows:
- A list of companies
- Interactive price charts
- Live statistics for the selected stock

**Technologies Used:**
- Backend: Python, FastAPI, SQLite, yfinance, pandas, scikit-learn
- Frontend: HTML, CSS, JavaScript
- Database: SQLite

**Challenges Faced:**
- Fixed CORS issues by adding middleware in FastAPI
- Handled missing stock data by adding a CSV fallback
- Verified database storage with a custom `check_db.py` script

---

## Screenshot
![Dashboard Screenshot](screenshots/dashboard.png)
