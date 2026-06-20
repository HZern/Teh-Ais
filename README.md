# Requirements

Install the required Python packages:

python3 -m pip install streamlit requests

The backend uses Python built-in libraries, so no extra backend packages are required.

# How to Run

You need to run the backend and frontend in two separate terminals.

## Terminal 1: Run the Backend

From the project root:

cd cloudConfigCheck
python3 security_backend.py

If successful, the backend will start at:

http://127.0.0.1:8000

The alerts endpoint is:

http://127.0.0.1:8000/alerts

You can test it by opening the alerts endpoint in a browser.

## Terminal 2: Run the Streamlit Frontend

From the project root:

cd cloudConfigCheck/frontend
python3 -m streamlit run pages/workload_analytics.py

Or, to open the security page directly:

cd cloudConfigCheck/frontend
python3 -m streamlit run pages/security_check.py

Streamlit will open the dashboard in your browser, usually at:

http://localhost:8501
