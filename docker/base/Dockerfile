FROM python:3.8-slim

COPY install.sh windscribe_login /tmp/
RUN bash -x /tmp/install.sh

CMD python /StockML/src/main.py