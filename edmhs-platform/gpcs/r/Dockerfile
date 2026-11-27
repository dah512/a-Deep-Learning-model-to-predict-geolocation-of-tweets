FROM rocker/r-ver:4.4.2
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpoppler-cpp-dev libsodium-dev poppler-utils \
 && apt-get clean \
 && Rscript -e 'install.packages(c("plumber","yaml","jsonlite","pdftools","testthat"), repos="https://packagemanager.posit.co/cran/__linux__/jammy/latest")'
WORKDIR /gpcs
COPY gpcs/r/ ./
COPY knowledge_base /knowledge_base
ENV GPCS_KB=/knowledge_base CORS_ORIGINS=http://localhost:4200
EXPOSE 8001
CMD ["Rscript", "-e", "plumber::pr_run(plumber::pr('plumber.R'), host='0.0.0.0', port=8001)"]
