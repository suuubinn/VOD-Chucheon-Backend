# from django.utils import timezone
# import pandas as pd
# import logging
# import json
# import os
# import pickle
# from django.conf import settings

# #reco1 : 장고 서버시간
# def get_server_time():
#     return timezone.now()    

# def get_assets_by_time(server_time):
#     time_view_df = pd.read_csv('static/time_view_df.csv',encoding='euc-kr')
#     server_hour = server_time.hour
#     selected_data = time_view_df[time_view_df['time_range'] == server_hour]['top_asset']
#     top_assets_list = selected_data.iloc[0].split(', ')
#     return top_assets_list

# def get_programs_by_assets(top_assets):
#     asset_df = pd.read_csv('static/asset_df.csv', encoding='euc-kr')
#     try:
#         selected_programs = asset_df[asset_df['asset_nm'].isin(top_assets)]
#         selected_programs = selected_programs.where(pd.notna(selected_programs), None)
#         if selected_programs.empty:
#             return pd.DataFrame()
#         return selected_programs
#     except Exception as e:
#         logging.exception(f"Error in get_programs_by_assets: {e}")
#         return pd.DataFrame()

# def get_programs_by_assets(top_assets):
#     asset_df = pd.read_csv('static/asset_df.csv', encoding='euc-kr')
#     try:
#         selected_programs = asset_df[asset_df['asset_nm'].isin(top_assets)]
#         if selected_programs.empty:
#             return pd.DataFrame()
#         return selected_programs
#     except Exception as e:
#         logging.exception(f"Error in get_programs_by_assets: {e}")
#         return pd.DataFrame()

# def load_recommendation_model(filename):
#     media_path = os.path.join(settings.MEDIA_ROOT, f'{filename}.pkl')
#     try:
#         with open(media_path, 'rb') as file:
#             recommendation_model = pickle.load(file)
#         return recommendation_model
#     except Exception as e:
#         print(f"Error loading model from file: {e}")
#         return None


from django.utils import timezone
import pandas as pd
import csv
import os
import pickle
from django.conf import settings
import boto3
import pandas as pd
from io import StringIO
from datetime import datetime
from hv_back import settings
import logging
import botocore.exceptions
import io


# 장고 서버시간
def get_server_time():
    return timezone.now()    

# react에 JsonResponse하는데, NaN response를 막기 위한 none 처리 함수
def convert_none_to_null_1(value):
    if pd.isna(value):
        return None
    return value

# react에 JsonResponse하는데, NaN response를 막기 위한 none 처리 함수
def convert_none_to_null(program):
    for key, value in program.items():
        if pd.isna(value):
            program[key] = None
    return program

# 로컬 모델을 불러오는 함수
def load_recommendation_model(filename):
    media_path = os.path.join(settings.MEDIA_ROOT, f'{filename}.pkl')
    try:
        with open(media_path, 'rb') as file:
            recommendation_model = pickle.load(file)
        return recommendation_model
    except Exception as e:
        print(f"Error loading model from file: {e}")
        return None
    
# 로컬 데이터 읽는 함수
def read_data_from_local(file_name):
    try:
        file_path = os.path.join('static', file_name)
        data = pd.read_csv(file_path, encoding='euc-kr')
        data = data.fillna(value={'disp_rtm': "null", "series_nm":"null"})  
        print(f'Successfully read data from: {file_path}')
        sample_data = data.head(1)
        print(f"Sample data: {sample_data}")
        return data
    except Exception as e:
        print(f'Error reading data from local file: {e}')
        raise e  

# 로깅 s3 버전으로 
S3_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
AWS_ACCESS_KEY = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_S3_REGION = settings.AWS_S3_REGION

def log_user_action(subsr, request, response):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_S3_REGION)
    log_file_path = 'data/daily_log.csv'
    file_content = ''  # 기본값으로 초기화
    # S3에서 로그 파일을 읽어옵니다.
    try:
        obj = s3.get_object(Bucket=S3_BUCKET_NAME, Key=log_file_path)
        file_content = obj['Body'].read().decode('euc-kr')
        file_exists = True
    except s3.exceptions.NoSuchKey:
        file_exists = False
    except botocore.exceptions.ClientError as e:
        logging.error(f"ClientError: {e.response['Error']['Message']}")
        file_exists = False  # ClientError 발생 시 처리

    # CSV 파일로 로그 데이터를 추가합니다.
    file_stream = io.StringIO(file_content)
    writer = csv.writer(file_stream)
    if not file_exists:
        writer.writerow(['subsr', 'Timestamp', 'Request Path', 'Method', 'Status Code'])

    writer.writerow([
        subsr,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        request.path,
        request.method,
        response.status_code
    ])

    # 수정된 내용을 S3에 다시 업로드합니다.
    s3.put_object(Bucket=S3_BUCKET_NAME, Key=log_file_path, Body=file_stream.getvalue())

# 로깅

# # AWS S3 버킷 이름
# bucket_name = "your-s3-bucket-name"

# def create_log_file_name():
#     # AWS 리전의 현재 시간을 고려하여 파일명 생성 (YYMMDD 형식)
#     region_time = datetime.now().strftime('%y%m%d')
#     return f"log_{region_time}.csv"

# def append_log_to_s3(log_entry, log_file_name):
#     # S3 클라이언트 생성
#     s3 = boto3.client('s3')

#     # 기존 로그 파일 내용 가져오기
#     try:
#         response = s3.get_object(Bucket=bucket_name, Key=log_file_name)
#         existing_log = response['Body'].read().decode('utf-8')
#     except s3.exceptions.NoSuchKey:
#         # 파일이 없는 경우 새로운 파일로 시작
#         existing_log = ""

#     # 새로운 로그 데이터 추가
#     updated_log = existing_log + log_entry + "\n"

#     # 업데이트된 로그를 S3에 업로드
#     s3.put_object(
#         Bucket=bucket_name,
#         Key=log_file_name,
#         Body=updated_log.encode('utf-8'),
#     )

# def log_request(request, response):
#     log_entry = {
#         'date': datetime.now().strftime('%Y-%m-%d'),
#         'time': datetime.now().strftime('%H:%M:%S'),
#         'user_id': request.user.id if request.user.is_authenticated else 'Anonymous',
#         'path': request.path,
#         'method': request.method,
#         'status_code': response.status_code,
#     }
#     # 로그 파일 이름 생성
#     log_file_name = create_log_file_name()
#     # 로그를 S3에 추가
#     append_log_to_s3(','.join(str(value) for value in log_entry.values()) + '\n', log_file_name)
