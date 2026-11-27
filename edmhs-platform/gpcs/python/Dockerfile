FROM python:3.12-slim
WORKDIR /app
COPY gpcs/python/pyproject.toml ./
COPY gpcs/python/gpcs ./gpcs
RUN pip install --no-cache-dir . anthropic
COPY knowledge_base /knowledge_base
ENV GPCS_KB=/knowledge_base
EXPOSE 8000
CMD ["uvicorn", "gpcs.api:app", "--host", "0.0.0.0", "--port", "8000"]
