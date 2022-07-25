import argparse
import os
import json
import plotly.graph_objects as go
import numpy as np
import math
from tqdm import tqdm
from plotly.subplots import make_subplots
import pandas as pd

############### TODO ###############
# visualization mode ("per_thread" or "per_cpu")
mode = 'per_thread'
####################################

def load_data(data_path):
    with open(data_path) as f:
        raw_data = json.load(f)
        cores = list(raw_data.keys())
        
        sched_info_dfs = {}
        for _, core in enumerate(cores):
            sched_data = raw_data[core]

            for name in sched_data:
                df = pd.json_normalize(sched_data[name])
                if 'Start Time' not in df: continue
                df['Name'] = str(name)
                df['Core'] = str(core)
                df['Duration'] = df['End Time'] - df['Start Time']
                df['Label'] = df['Name'] + '(' + df['PID'].astype(str) + ')'
                df['StartTime'] = df['Start Time']
                if core not in sched_info_dfs:
                    sched_info_dfs[core] = df
                else:                    
                    sched_info_dfs[core] = pd.concat([sched_info_dfs[core],df])

    return sched_info_dfs

def visualize_all_cores_per_thread(sched_info_dfs):
    config = dict({'scrollZoom': True})

    fig = go.Figure(
    layout = {
        'barmode': 'stack',
        'xaxis': {'automargin': True},
        'yaxis': {'automargin': True}}#, 'categoryorder': 'category ascending'}}
    )

    for core in sched_info_dfs:
        for pid, pid_df in tqdm(sched_info_dfs[core].groupby('PID')): 
            fig.add_bar(x=pid_df.Duration,
                y=pid_df.Label,
                base=pid_df.StartTime,
                orientation='h',
                showlegend=False,
                name=pid)

        fig.update_layout(
            title=core+" scheduling",
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

def visualize_all_cores_per_cpu(sched_info_dfs):
    config = dict({'scrollZoom': True})

    fig = go.Figure(
    layout = {
        'barmode': 'stack',
        'xaxis': {'automargin': True},
        'yaxis': {'automargin': True}}#, 'categoryorder': 'category ascending'}}
    )

    for core in sched_info_dfs:
        df = sched_info_dfs[core]
        fig.add_bar(x=df.Duration,
                    y=df.Core,
                    base=df.StartTime,
                    orientation='h',
                    showlegend=False,
                    text=df.Label
                    )

        fig.update_layout(
            title="All scheduling",
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
    sched_info_dfs = load_data(file_path)
    if mode == 'per_thread':
        visualize_all_cores_per_thread(sched_info_dfs)
    elif mode == 'per_cpu':
        visualize_all_cores_per_cpu(sched_info_dfs)