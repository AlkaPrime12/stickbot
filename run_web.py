import uvicorn
from app.logging_config import setup_logging


if __name__ == "__main__":
    setup_logging()
    uvicorn.run("app.web.main:app", host="0.0.0.0", port=8000, reload=False)
