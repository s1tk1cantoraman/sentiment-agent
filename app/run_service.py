import uvicorn

from core import settings


if __name__ == "__main__":
    uvicorn.run("service:app", host=settings.HOST, port=settings.PORT, reload=settings.is_dev())
    
    
#TODO:
# - refactor service.py
# - refactor streamlit_app.py
# - refactor readme
# - create fresh requirements.txt with pip freeze > requirements.txt
# - add error handling
# - add a tool to the agent to ensure structured output
# - remove unused code
# - understand logging requirements and implement them
# - add init to agents folder
# - test with env variables removed and fresh install
# - ask claude for coding best practices 
# - push to github
# - learn streamlit properly