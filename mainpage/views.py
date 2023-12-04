import os
import boto3
import random
from botocore.exceptions import NoCredentialsError
import pandas as pd
from django.http import JsonResponse
from rest_framework.response import Response
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
import json
from hv_back.utils import get_assets_by_time
from hv_back.utils import get_programs_by_assets
from hv_back.utils import get_server_time


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

def convert_none_to_null(value):
    if pd.isna(value):
        return None
    return value


# 로컬로 데이터 읽는 코드
def read_data_from_local(file_name):
    try:
        file_path = os.path.join('static', file_name)
        data = pd.read_csv(file_path, encoding='euc-kr')
        
        # NaN 값을 적절한 값으로 대체
        data = data.fillna(value={'disp_rtm': "null", "series_nm":"null"})  # your_column_name과 your_default_value를 적절히 수정'''
        
        print(f'Successfully read data from: {file_path}')
        sample_data = data.head(1)
        print(f"Sample data: {sample_data}")  # 변경된 부분
        return data
    except Exception as e:
        print(f'Error reading data from local file: {e}')
        raise e  
    

@method_decorator(csrf_exempt, name='dispatch')  # CSRF 토큰 무시
class RecommendationView_1(View):
    def post(self, request):
        try:
            server_time = get_server_time()
            print(f'server_time, {server_time}')
            top_assets = get_assets_by_time(server_time)
            print(f'top_assets, {top_assets}')
            selected_programs = get_programs_by_assets(top_assets)
            # result_data = selected_programs.to_dict('records')
            result_data = selected_programs.apply(lambda x: x.map(convert_none_to_null)).to_dict('records')


            # for program in selected_programs:
            #     if isinstance(program, dict):
            #         result_data.append({'asset_nm': program.get('asset_nm'), 'image': program.get('image')})
            print(f'result_data, {result_data}')
            return JsonResponse({'data': result_data}, content_type='application/json')

        except Exception as e:
            logging.exception(f"Error in RecommendationView: {e}")
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
    
# def get_programs_by_genre(genre):
#     program_data = read_data_from_s3(AWS_S3_CUSTOM_DOMAIN, PROGRAM_OBJECT_KEY)
#     genre_programs = program_data[program_data['genre_of_ct_cl'] == genre]
#     programs = [{'asset_nm': row['asset_nm'], 'image': row['image']} for _, row in genre_programs.iterrows()]
#     return programs


# reco2 : 장르기반 프로그램 뽑는 함수
def get_programs_by_genre(genre):
    program_data = read_data_from_local('asset_df.csv')
    genre_programs = program_data[program_data['category_l'] == genre]
    genre_programs = genre_programs.where(pd.notna(genre_programs), None)
    programs = genre_programs.to_dict('records')
    return programs


# reco2 : 사용자 장르 찾는 함수
def get_most_watched_genre(subsr):
    subsr_data = read_data_from_local('subsr_max_genre.csv')
    print(f"subsr_data: {subsr_data}")
    try:
        subsr_genre = subsr_data.loc[subsr_data['subsr'].astype(str) == str(subsr), 'top_genres'].iloc[0]
        subsr_genre = eval(subsr_genre)[0] if subsr_genre else None
    except IndexError:
        subsr_genre = None
    return subsr_genre


# reco2 : 예외처리를 위한 랜덤 뽑아주기
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
            print(f"genre!: {most_watched_genre}")
            if most_watched_genre is not None:
                print(f"genre not none!")
                programs = get_programs_by_genre(most_watched_genre)
            else:
                programs = get_random_programs(20)
                print(f"genre none")
            # 아래의 로그도 추가
            # print(f"First program: {programs[0]}")
            if not programs:
                return JsonResponse({'error': 'No programs available'}, status=404)
            num_programs_to_select = min(20, len(programs))
            selected_programs = programs if num_programs_to_select >= len(programs) else random.sample(programs, num_programs_to_select)
            # result_data = selected_programs
            result_data = [convert_none_to_null(program) for program in selected_programs]
            return JsonResponse({'data': result_data}, content_type='application/json')

        except Exception as e:
            logging.exception(f"Error in RecommendationView_2: {e}")
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
        


@method_decorator(csrf_exempt, name='dispatch')
class SearchVeiw(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            program_to_search = data.get('programName', None) 
            print(f"program_to_search:", {program_to_search})
            if not program_to_search:
                return JsonResponse({'error': 'program_to_search is missing'}, status=400)
            try:
                asset_df = read_data_from_local('asset_df.csv')
            except Exception as e:
                logging.exception(f"Error reading data from local file: {e}")
                return JsonResponse({'error': 'Failed to read data file'}, status=500)
            try:
                selected_data = asset_df[asset_df['asset_nm'].str.contains(program_to_search)]
            except KeyError:
                return JsonResponse({'error': 'Invalid filtering condition'}, status=400)
            result_data = selected_data.where(pd.notna(selected_data), None).applymap(convert_none_to_null).to_dict('records')
            return JsonResponse({'data': result_data})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logging.exception(f"Error in ProcessButtonClickView: {e}")
            return JsonResponse({'error': 'Internal Server Error'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')  
class ProcessButtonClickView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            button_text = data.get('button_text')
            print(f"button_text: {button_text}")
            if not button_text:
                return JsonResponse({'error': 'Button text is missing'}, status=400)
            try:
                asset_df = read_data_from_local('asset_df.csv')
            except Exception as e:
                logging.exception(f"Error reading data from local file: {e}")
                return JsonResponse({'error': 'Failed to read data file'}, status=500)
            try:
                selected_data = asset_df[asset_df['category_h'] == button_text]
            except KeyError:
                return JsonResponse({'error': 'Invalid filtering condition'}, status=400)
            result_data = selected_data.where(pd.notna(selected_data), None).applymap(convert_none_to_null).to_dict('records')

            return JsonResponse({'data': result_data})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logging.exception(f"Error in ProcessButtonClickView: {e}")
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
        

