FROM asia.gcr.io/angelic-shift-296514/stockml-base:v0

COPY install.sh requirements.txt /tmp/
RUN bash -x /tmp/install.sh

CMD python /StockML/src/main.py