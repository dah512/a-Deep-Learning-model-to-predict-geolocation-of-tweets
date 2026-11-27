FROM python:3.12-slim
WORKDIR /app
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY gpcs/python/gpcs ./gpcs
COPY services/api/app ./app
COPY knowledge_base /knowledge_base
ENV GPCS_KB=/knowledge_base
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
