FROM python:3.8
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE casper.settings
ENV ENVIRONMENT 'development'
ENV DATABASE_NAME 'casper_db'
ENV DATABASE_USER 'root'
ENV DATABASE_PASS 'l3t$D01t'
ENV DATABASE_HOST 'casper_db'
ENV DATABASE_PORT '3306'

RUN mkdir /casper
COPY ./ /casper
VOLUME ["/casper"]

# entrypoint
COPY docker-entrypoint.sh /entrypoint.sh
RUN [ "chmod", "755", "/entrypoint.sh" ]
ENTRYPOINT [ "/entrypoint.sh" ]

EXPOSE 8000

WORKDIR /casper

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]