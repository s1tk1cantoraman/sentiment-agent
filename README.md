# 🧰 AI Agent Service Toolkit

A toolkit for running an AI agent service built with LangGraph, FastAPI and Streamlit.

It includes a [LangGraph](https://langchain-ai.github.io/langgraph/) agent, a [FastAPI](https://fastapi.tiangolo.com/) service to serve it, a client to interact with the service, and a [Streamlit](https://streamlit.io/) app that uses the client to provide a chat interface. Data structures and settings are built with [Pydantic](https://github.com/pydantic/pydantic).

## Overview

### Quickstart

1. Set up environment variables:
   Create a `.env` file in the root directory with at least one LLM API key:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Run the FastAPI server:
   ```sh
   python app/run_service.py
   ```

4. In a separate terminal, run the Streamlit app:
   ```sh
   streamlit run app/streamlit_app.py
   ```

### Key Features

1. **LangGraph Agent**: A customizable agent built using the LangGraph framework
2. **FastAPI Service**: Serves the agent with both streaming and non-streaming endpoints
3. **Streamlit Interface**: Provides a user-friendly chat interface for interacting with the agent
4. **Asynchronous Design**: Utilizes async/await for efficient handling of concurrent requests
5. **Dynamic Metadata**: `/info` endpoint provides dynamically configured metadata about the service
6. **Centralized Error Handling**: Consistent error handling across all API endpoints
7. **Database Logging**: Comprehensive logging system with database storage for persistent logs
8. **Robust Thread Management**: Safe handling of empty or new conversation threads

### Project Structure

The repository is structured as follows:

- `app/agents/`: Defines the sentiment analysis agent and other agents
- `app/schema/`: Defines the protocol schema and data models
- `app/core/`: Core modules including LLM definition, settings, utilities and error handling
- `app/service/`: FastAPI service implementation
- `app/streamlit_app.py`: Streamlit app providing a chat interface
- `requirements.txt`: Project dependencies

#### Core Architecture

- **Utility Functions**: Common utilities like exception handling are centralized in `app/core/utils.py`
- **Error Handling**: The `CoreUtils` class provides decorators that ensure consistent error handling across all API endpoints
- **Logging System**: Configurable logging with database storage for easier debugging and monitoring

### Environment Variables

The following environment variables can be configured:

- `OPENAI_API_KEY`: API key for OpenAI models
- `HOST`: Host to run the service on (default: "0.0.0.0")
- `PORT`: Port to run the service on (default: 8081)
- `AUTH_SECRET`: Secret for authentication (optional)
- `LANGCHAIN_TRACING_V2`: Enable LangChain tracing (default: false)
- `LANGCHAIN_PROJECT`: LangChain project name (default: "default")
- `LANGCHAIN_ENDPOINT`: LangChain endpoint URL
- `LANGCHAIN_API_KEY`: LangChain API key
- `OPENWEATHERMAP_API_KEY`: API key for OpenWeatherMap (optional)
- `LOG_LEVEL`: Logging level (default: "INFO")
- `LOG_DB_PATH`: Path to store log database (default: "logs/logs.db")

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
