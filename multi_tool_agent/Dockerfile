FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir google-adk pymongo python-dotenv

COPY . .

EXPOSE 8000

CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8000", "multi_tool_agent"]