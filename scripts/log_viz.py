import argparse
from distutils.command.config import config
import os
import json
import sched
import plotly.graph_objects as go
import numpy as np
import math
from tqdm import tqdm
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd

############### TODO ###############
# visualization mode ("per_thread" or "per_cpu")
mode = 'per_instance'
# Skip threshold (s)
SKIP_THRESHOLD = 0.0005
# Additional features ( skip )
features = ['skip']
####################################

def load_data(data_path, config_path):
    sched_info_df = pd.DataFrame()
    with open(config_path) as f:
        config_data = json.load(f)
    with open(data_path) as f:
        raw_data = json.load(f)
    cores = list(raw_data.keys())
        
    for _, core in enumerate(cores):
        sched_data = raw_data[core]
        for name in sched_data:
            if config_data[name]:
                df = pd.json_normalize(sched_data[name])
                if 'StartTime' not in df: continue
                df['Core'] = core
                df['Name'] = str(name) + '(' + df['PID'].astype(str) + ')'
                df['Core'] = str(core)
                df['Duration'] = df['EndTime'] - df['StartTime']
                df['StartTime'] = df['StartTime']
                df['Instance'] = df['Instance']
                
                if 'skip' in features:
                    df = df[df.Duration >= SKIP_THRESHOLD]
                
                if df.size == 0: continue
                
                if sched_info_df.size == 0:
                    sched_info_df = df
                else:                    
                    sched_info_df = pd.concat([sched_info_df,df])

    return sched_info_df

def visualize_per_thread(sched_info_df):
    config = dict({'scrollZoom': True})

    for core, core_df in tqdm(sched_info_df.groupby('Core')):
        fig = px.bar(core_df, base='StartTime', x='Duration', y='Name', color='Name', hover_data=['Instance'])
        
        if 'skip' in features:
            title=core+' scheduling (Skip threshold: '+str(SKIP_THRESHOLD*1000)+'ms)'
        else:
            title=core+' scheduling'
        
        fig.update_layout(
            title=title,
            xaxis_title="time (s)",
            barmode='stack',
            font=dict(
                family="Courier New, monospace",
                size=8,
                color="#7f7f7f"
            )
        )
        fig.show()
        
    return

def visualize_per_cpu(sched_info_df):
    config = dict({'scrollZoom': True})
    
    fig = px.bar(sched_info_df, base='StartTime', x='Duration', y='Core', color='Name', text='Name', hover_data=['EndTime', 'Instance'])

    if 'skip' in features:
        title='Scheduling (Skip threshold: '+str(SKIP_THRESHOLD*1000)+'ms)'
    else:
        title='Scheduling'
    
    fig.update_layout(
        title=title,
        xaxis_title="time (s)",
        barmode='stack',
        font=dict(
            family="Courier New, monospace",
            color="#7f7f7f"
        )
    )
            
    fig.show()
    
def visualize_per_instance(sched_info_df):
    config = dict({'scrollZoom': True})
    
    sched_info_df = sched_info_df[sched_info_df['Instance'] != -1]
    fig = px.bar(sched_info_df, base='StartTime', x='Duration', y='Core', color='Instance', text='Name', hover_data=['EndTime', 'Instance'])

    if 'skip' in features:
        title='Scheduling per instance (Skip threshold: '+str(SKIP_THRESHOLD*1000)+'ms)'
    else:
        title='Scheduling per instance'
    
    fig.update_layout(
        title=title,
        xaxis_title="time (s)",
        barmode='stack',
        font=dict(
            family="Courier New, monospace",
            color="#7f7f7f"
        )
    )
            
    fig.show()

if __name__ == '__main__':
    data_path = os.path.dirname(os.path.realpath(__file__))[0:-7] + "/data/sample.json"
    # data_path = os.path.dirname(os.path.realpath(__file__))[0:-7] + "/data/ftrace_parse_data.json"
    config_path = os.path.dirname(os.path.realpath(__file__))[0:-7] + "/filtering_option.json"

    sched_info_df = load_data(data_path, config_path)
    if mode == 'per_thread':
        visualize_per_thread(sched_info_df)
    elif mode == 'per_cpu':
        visualize_per_cpu(sched_info_df)
    elif mode == 'per_instance':
        visualize_per_instance(sched_info_df)