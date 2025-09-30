FROM kong/deck:latest

WORKDIR /kong

COPY kong.yml .
COPY setup.sh .

RUN chmod +x setup.sh

CMD ["./setup.sh"]