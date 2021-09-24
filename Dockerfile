FROM python:3.8

COPY ./ /final
WORKDIR /final

RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]