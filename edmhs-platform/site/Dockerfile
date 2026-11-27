FROM python:3.12-slim AS build
WORKDIR /src
RUN pip install --no-cache-dir markdown
COPY docs ./docs
COPY site ./site
RUN python site/build.py
FROM nginx:1.27-alpine
COPY --from=build /src/site/edmhs-org /usr/share/nginx/html
