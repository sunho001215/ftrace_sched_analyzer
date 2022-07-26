import argparse
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
mode = 'per_thread'
# Skip threshold (s)
SKIP_THRESHOLD = 0.001
# Additional features ( skip )
features = ['skip']
####################################

def load_data(data_path):
    sched_info_df = pd.DataFrame()
    
    with open(data_path) as f:
        raw_data = json.load(f)
        cores = list(raw_data.keys())
        
        for _, core in enumerate(cores):
            sched_data = raw_data[core]
            
            for name in sched_data:
                df = pd.json_normalize(sched_data[name])
                if 'Start Time' not in df: continue
                df['Core'] = core
                df['Name'] = str(name) + '(' + df['PID'].astype(str) + ')'
                df['Core'] = str(core)
                df['Duration'] = df['End Time'] - df['Start Time']
                df['Label'] = 'Duration(ms): ' + str(df['Duration']*1000)
                df['StartTime'] = df['Start Time']
                
                
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
        fig = px.bar(core_df, base='StartTime', x='Duration', y='Name', color='Name')
        
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
    
    fig = px.bar(sched_info_df, base='StartTime', x='Duration', y='Core', color='Name', text='Name')


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

if __name__ == '__main__':
    file_path = os.path.dirname(os.path.realpath(__file__))[0:-7] + "/data/sample.json"
    # file_path = os.path.dirname(os.path.realpath(__file__))[0:-7] + "/data/ftrace_parse_data.json"
    sched_info_df = load_data(file_path)
    if mode == 'per_thread':
        visualize_per_thread(sched_info_df)
    elif mode == 'per_cpu':
        visualize_per_cpu(sched_info_df)