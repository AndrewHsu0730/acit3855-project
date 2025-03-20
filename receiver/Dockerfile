FROM python:3

LABEL maintainer="chsu100@my.bcit.ca"

RUN mkdir /app /app/logs

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

RUN chown -R nobody:nogroup /app
USER nobody

EXPOSE 8080

ENTRYPOINT [ "python3" ]

CMD [ "app.py" ]