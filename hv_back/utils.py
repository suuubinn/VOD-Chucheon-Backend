from django.utils import timezone
import pandas as pd
import logging
import json

#reco1 : 장고 서버시간
def get_server_time():
    return timezone.now()    

def get_assets_by_time(server_time):
    time_view_df = pd.read_csv('static/time_view_df.csv',encoding='euc-kr')
    server_hour = server_time.hour
    selected_data = time_view_df[time_view_df['time_range'] == server_hour]['top_asset']
    top_assets_list = selected_data.iloc[0].split(', ')
    return top_assets_list

def get_programs_by_assets(top_assets):
    asset_df = pd.read_csv('static/asset_df.csv', encoding='euc-kr')
    try:
        selected_programs = asset_df[asset_df['asset_nm'].isin(top_assets)]
        selected_programs = selected_programs.where(pd.notna(selected_programs), None)
        if selected_programs.empty:
            return pd.DataFrame()
        return selected_programs
    except Exception as e:
        logging.exception(f"Error in get_programs_by_assets: {e}")
        return pd.DataFrame()

def get_programs_by_assets(top_assets):
    asset_df = pd.read_csv('static/asset_df.csv', encoding='euc-kr')
    try:
        selected_programs = asset_df[asset_df['asset_nm'].isin(top_assets)]
        if selected_programs.empty:
            return pd.DataFrame()
        return selected_programs
    except Exception as e:
        logging.exception(f"Error in get_programs_by_assets: {e}")
        return pd.DataFrame()
