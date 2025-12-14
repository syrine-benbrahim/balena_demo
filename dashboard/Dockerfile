FROM python:3

WORKDIR /app
RUN pip install flask

COPY server.py .
COPY index.html .

CMD ["python", "server.py"]
