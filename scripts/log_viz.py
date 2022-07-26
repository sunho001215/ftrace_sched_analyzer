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
import csv

############### TODO ###############
# visualization mode ("per_thread" or "per_cpu")
mode = 'per_cpu'
# Skip threshold (s)
SKIP_THRESHOLD = 0.0005
# Showing e2e instance
# Additional features ( skip, e2e )
features = ['e2e']
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

def visualize_per_thread(sched_info_df, e2e_response_time_path='None', e2e_instance_range=[0,0]):
    config = dict({'scrollZoom': True})

    for core, core_df in tqdm(sched_info_df.groupby('Core')):
        fig = px.bar(core_df, base='StartTime', x='Duration', y='Name', color='Name', hover_data=['Instance'])
        
        if 'skip' in features:
            title=core+' scheduling (Skip threshold: '+str(SKIP_THRESHOLD*1000)+'ms)'
        else:
            title=core+' scheduling'
            
        if 'e2e' in features:
            draw_e2e_instance(fig, e2e_response_time_path, e2e_instance_range)
        
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

def visualize_per_cpu(sched_info_df, e2e_response_time_path='None', e2e_instance_range=[0,0]):
    config = dict({'scrollZoom': True})
    
    fig = px.bar(sched_info_df, base='StartTime', x='Duration', y='Core', color='Name', text='Name', hover_data=['EndTime', 'Instance'])

    if 'skip' in features:
        title='Scheduling (Skip threshold: '+str(SKIP_THRESHOLD*1000)+'ms)'
    else:
        title='Scheduling'
        
    if 'e2e' in features:
        draw_e2e_instance(fig, e2e_response_time_path, e2e_instance_range)
    
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
    
def visualize_per_instance(sched_info_df, e2e_response_time_path='None', e2e_instance_range=[0,0]):
    config = dict({'scrollZoom': True})
    
    sched_info_df = sched_info_df[sched_info_df['Instance'] != -1]
    fig = px.bar(sched_info_df, base='StartTime', x='Duration', y='Core', color='Instance', text='Name', hover_data=['EndTime', 'Instance'])

    if 'skip' in features:
        title='Scheduling per instance (Skip threshold: '+str(SKIP_THRESHOLD*1000)+'ms)'
    else:
        title='Scheduling per instance'
        
    if 'e2e' in features:
        draw_e2e_instance(fig, e2e_response_time_path, e2e_instance_range)
    
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

def draw_e2e_instance(fig, e2e_response_time_path, e2e_instance_range):
    if e2e_response_time_path == 'None': return
    
    e2e_info = []
    with open(e2e_response_time_path) as f:
        reader = csv.reader(f)
        for line in reader:
            e2e_info.append({'Start':float(line[0]), 'End':float(line[1]), 'Instance':int(line[2])})
    
    for e2e in e2e_info:
        if e2e['Instance'] >= e2e_instance_range[0] and e2e['Instance'] < e2e_instance_range[1]:
            fig.add_vrect(x0=e2e['Start'], x1=e2e['End'], annotation_text=e2e['Instance'], annotation_position='top left', fillcolor='green', opacity=0.1, line_width=3)
            
    return

if __name__ == '__main__':
    data_path = os.path.dirname(os.path.realpath(__file__))[0:-7] + "/data/sample.json"
    # data_path = os.path.dirname(os.path.realpath(__file__))[0:-7] + "/data/ftrace_parse_data.json"
    config_path = os.path.dirname(os.path.realpath(__file__))[0:-7] + "/filtering_option.json"
    
    e2e_response_time_path = '/Users/hayeonp/git/ftrace_sched_analyzer/data/sample_e2e.csv'

    sched_info_df = load_data(data_path, config_path)
    if mode == 'per_thread':
        visualize_per_thread(sched_info_df, e2e_response_time_path=e2e_response_time_path, e2e_instance_range=[895, 918])
    elif mode == 'per_cpu':
        visualize_per_cpu(sched_info_df, e2e_response_time_path=e2e_response_time_path, e2e_instance_range=[895, 918])
    elif mode == 'per_instance':
        visualize_per_instance(sched_info_df, e2e_response_time_path=e2e_response_time_path, e2e_instance_range=[895, 918])