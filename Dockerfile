FROM --platform=linux/amd64 python:3.10

# 필요한 라이브러리 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    # 다른 필요한 라이브러리 추가 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt ./

# scikit-surprise 설치가 문제일 경우를 대비해 추가
RUN pip install -r requirements.txt

COPY . .

# 포트 개방/ 플라스크나 장고에서만 수행
EXPOSE 80
CMD ["python", "manage.py", "runserver", "0.0.0.0:80"]