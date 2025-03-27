import uvicorn

from core import settings


if __name__ == "__main__":
    uvicorn.run("service:app", host=settings.HOST, port=settings.PORT, reload=settings.is_dev())
    
    
#TODO:
# - refactor readme
# - create fresh requirements.txt with pip freeze > requirements.txt
# - add error handling
# - remove unused code
# - understand logging requirements and implement them
# - test with env variables removed and fresh install
# - ask claude for coding best practices 
# - push to github
# - learn streamlit properly

# Added support for error handling but havent implemented it yet
# thread remove is not working
# there is no logging yet