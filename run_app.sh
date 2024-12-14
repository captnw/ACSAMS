echo Navigating to python virtual environment and starting app
cd .venv/Scripts && source activate && cd ../.. && uvicorn main:app --reload --log-level debug