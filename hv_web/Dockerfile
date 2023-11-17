FROM python

RUN apt-get update && apt-get install -y --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

#포트 개방/ 플라스크나 장고에서만 수행
EXPOSE 80
CMD ["python","manage.py","runserver","0.0.0.0:80"]