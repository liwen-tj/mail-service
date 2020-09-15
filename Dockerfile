FROM python:3.7-alpine
MAINTAINER liwen-tj "liwen00812@qq.com"

WORKDIR /
COPY . /
RUN pip3 install -r requirements.txt

EXPOSE 5000
CMD ["python", "app.py"]
