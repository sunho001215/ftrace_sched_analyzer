import argparse
import os
import json
import plotly.graph_objects as go
import numpy as np
import math
from tqdm import tqdm
from plotly.subplots import make_subplots


############### TODO ###############
# select cores to visualize
core_plot = [10, 11]
# visualization mode ("per_thread" or "per_cpu")
mode = 'per_cpu'
# computtion speed ("fast" or "normal") -> normal will skip data little than 100ns
speed = 'normal' 
####################################

class CoreInfo:
    def __init__(self, core):
        self.core = core
        self.min = math.inf
        self.max = -math.inf
        self.processes = {}
        return
    
    def add(self, name, pid, start, end):
        if speed == 'fast' and end-start < 0.001: return

        pid = str(pid)
        if pid not in self.processes:
            self.processes[pid] = {'name':[], 'start':[], 'end':[], 'len':[], 'label':[]}
        self.processes[pid]['name'].append(name+'('+pid+')')
        self.processes[pid]['start'].append(start)
        self.processes[pid]['end'].append(end)
        self.processes[pid]['len'].append(end-start)

        self.processes[pid]['label'].append('name: ' + name + ' / pid:' + str(pid) + ' / len:'+ str(end-start) +' / start:' + str(start) + ' / end:' + str(end))

        return
    
    def update_min_max(self):
        for pid in self.processes:
            if self.min == math.inf:
                self.min = min(self.processes[pid]['start'])
                self.max = max(self.processes[pid]['end'])
            else:
                cur_min = min(self.processes[pid]['start'])
                cur_max = max(self.processes[pid]['end'])
                self.min = min(cur_min, self.min)
                self.max = max(cur_max, self.max)

def load_data(data_path):
    with open(data_path) as f:
        raw_data = json.load(f)
        cores = list(raw_data.keys())
        
        core_info_data = []
        for _, core in enumerate(cores):
            core_info = CoreInfo(core)
            core_data = raw_data[core]

            for name in core_data:
                for process_info in core_data[name]:
                    pid = process_info['PID']
                    start = process_info['Start Time']
                    end = process_info['End Time']
                    core_info.add(name, pid, start, end)

            core_info.update_min_max()
            core_info_data.append(core_info)
    
    return core_info_data

def visualize_all_cores(core_info_data):
    config = dict({'scrollZoom': True})

    if mode == "per_cpu":
        fig = make_subplots(rows=1, cols=1)
    else:
        subplot_names = []
        for i in range(len(core_plot)):
            subplot_names.append('cpu'+str(core_plot[i]))

        fig = make_subplots(rows=len(core_plot), cols=1, subplot_titles=subplot_names)
    
    ax_range = [math.inf, -math.inf]
    for core_info in core_info_data:
        ax_range[0] = min(core_info.min, ax_range[0])
        ax_range[1] = max(core_info.max, ax_range[1])

    for core_info in core_info_data:
        print('Plotting '+core_info.core+'...')
        for pid in tqdm(core_info.processes):
            info = core_info.processes[pid]
            
            is_core = False
            idx = 0
            for i in range(len(core_plot)):
                if core_info.core == 'cpu'+str(core_plot[i]):
                    is_core = True
                    idx = i + 1
            if not is_core:
                continue
            
            if mode == "per_cpu":
                for i in range(len(info['name'])):
                    fig.add_trace(go.Bar(
                        y=[core_info.core],
                        x=[info['len'][i]],
                        base=[info['start'][i]],
                        text=[info['name'][i]],
                        hovertext=[info['label'][i]],
                        textposition='auto',
                        orientation='h',
                        showlegend=False
                    ), row=1, col=1)
            else:
                for i in range(len(info['name'])):
                    fig.add_trace(go.Bar(
                        y=[info['name'][i]],
                        x=[info['len'][i]],
                        base=[info['start'][i]],
                        text=[info['name'][i]],
                        hovertext=[info['label'][i]],
                        textposition='auto',
                        orientation='h',
                        showlegend=False
                    ), row=idx, col=1)
    
    fig.update_layout(
        title="Analysis Result",
        xaxis_title="time (s)",
        barmode='stack',
        font=dict(
            family="Courier New, monospace",
            size=18,
            color="#7f7f7f"
        )
    )
    
    if mode == "per_cpu":
        fig.update_xaxes(range=ax_range, row=1, col=1)
    else:
        for i in range(len(core_plot)):
            fig.update_xaxes(range=ax_range, row=i+1, col=1)
    
    fig.show(config=config)
    
    return


if __name__ == '__main__':
    # file_path = os.path.dirname(os.path.realpath(__file__))[0:-7] + "/sample.json"
    file_path = os.path.dirname(os.path.realpath(__file__))[0:-7] + "/ftrace_parse_data.json"
    core_info_data = load_data(file_path)
    visualize_all_cores(core_info_data)