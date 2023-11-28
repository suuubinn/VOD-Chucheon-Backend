import os
import boto3
import random
from botocore.exceptions import NoCredentialsError
import pandas as pd
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
import json
# def read_data_from_s3(bucket_name, object_key):
#     try:
#         s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)
#         response = s3.get_object(Bucket=bucket_name, Key=object_key)
#         data = pd.read_csv(response['Body'])

#         return data
#     except NoCredentialsError as e:
#         print('AWS credentials not available')
#         raise e
#     except Exception as e:
#         print(f'Error reading data from S3: {e}')
#         raise e
def read_data_from_local(file_name):
    try:
        file_path = os.path.join('static', file_name)
        data = pd.read_csv(file_path, encoding='euc-kr')
        print(f'Successfully read data from: {file_path}')
        sample_data = data.head(1)
        print(f"Sample data: {sample_data}")  # 변경된 부분
        return data
    except Exception as e:
        print(f'Error reading data from local file: {e}')
        raise e  
# def get_programs_by_genre(genre):
#     program_data = read_data_from_s3(AWS_S3_CUSTOM_DOMAIN, PROGRAM_OBJECT_KEY)
#     genre_programs = program_data[program_data['genre_of_ct_cl'] == genre]
#     programs = [{'asset_nm': row['asset_nm'], 'image': row['image']} for _, row in genre_programs.iterrows()]
#     return programs

def get_programs_by_genre(genre):
    program_data = read_data_from_local('asset_df.csv')
    genre_programs = program_data[program_data['genre_of_ct_cl'] == genre]
    programs = [{'asset_nm': row['asset_nm'], 'image': row['image'] if not pd.isna(row['image']) else None} for _, row in genre_programs.iterrows()]
    return programs

def get_most_watched_genre(subsr):
    log_data = read_data_from_local('vod_pp_df.csv')
    user_logs = log_data[log_data['subsr'] == subsr]
    genre_counts = user_logs['genre_of_ct_cl'].value_counts()
    if not genre_counts.empty:
        most_watched_genre = genre_counts.sort_values(ascending=False).index[0]
    else:
        most_watched_genre = None

    return most_watched_genre



def get_random_programs(num_programs):
    program_data = read_data_from_local('asset_df.csv')

    try:
        if not program_data.empty:
            selected_programs = program_data.sample(min(num_programs, len(program_data)))
            programs = [{'asset_nm': row['asset_nm'], 'image': row['image'] if not pd.isna(row['image']) else None} for _, row in selected_programs.iterrows()]
            return programs
        else:
            return []
    except Exception as e:
        logging.exception(f"Error in get_random_programs: {e}")
        return []
    
@method_decorator(csrf_exempt, name='dispatch')  # CSRF 토큰 무시/
class RecommendationView_2(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            subsr = data.get('subsr', None)
            print(f"Received subsr: {subsr}")
            if not subsr:
                return JsonResponse({'error': 'subsr is required'}, status=400)
            most_watched_genre = get_most_watched_genre(subsr)
            if most_watched_genre is not None:
                print(f"genre!: {most_watched_genre}")
                programs = get_programs_by_genre(most_watched_genre)
            else:
                programs = get_random_programs(20)
            # 아래의 로그도 추가
            # print(f"First program: {programs[0]}")
            print(f"fav genre: {most_watched_genre}")
            if not programs:
                return JsonResponse({'error': 'No programs available'}, status=404)
            num_programs_to_select = min(20, len(programs))
            selected_programs = programs if num_programs_to_select >= len(programs) else random.sample(programs, num_programs_to_select)
            result_data = [{'asset_nm': program['asset_nm'], 'image': program['image']} for program in selected_programs]
            return JsonResponse({'data': result_data}, content_type='application/json')

        except Exception as e:
            logging.exception(f"Error in RecommendationView_2: {e}")
            return JsonResponse({'error': 'Internal Server Error'}, status=500)