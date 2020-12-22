FROM asia.gcr.io/angelic-shift-296514/stockml-base:v0

COPY StockML /StockML
RUN bash -x /StockML/docker/app/install.sh

CMD python /StockML/src/main.py