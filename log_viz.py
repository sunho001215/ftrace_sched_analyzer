import argparse
import os
import json
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots


class CoreInfo:
    def __init__(self, core):
        self.core = core
        self.min = -1
        self.max = -1
        self.processes = {}
        return
    
    def add(self, name, pid, start, end):
        pid = str(pid)
        if pid not in self.processes:
            self.processes[pid] = {'name':[], 'start':[], 'end':[], 'len':[], 'label':[]}
        self.processes[pid]['name'].append(name+'('+pid+')')
        self.processes[pid]['start'].append(start)
        self.processes[pid]['end'].append(end)
        self.processes[pid]['len'].append(end-start)
        self.processes[pid]['label'].append('name: ' + name + ' / pid:' + str(pid) + ' / start:' + str(start) + ' / end:' + str(end))
    
    def update_min_max(self):        
        for pid in self.processes:
            if self.min == -1:
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
    fig = make_subplots(rows=1, cols=1)
    
    range = [-1, -1]
    for core_info in core_info_data:
        if range[0] == -1:
            range[0] = core_info.min
            range[1] = core_info.max
        else:
            range[0] = min(core_info.min, range[0])
            range[1] = max(core_info.max, range[1])
    
    
    for core_info in core_info_data:
        for pid in core_info.processes:
            info = core_info.processes[pid]
            if core_info.core != 'cpu11': continue
            
            fig.add_trace(go.Bar(
                y=[core_info.core],
                base=info['start'],
                x=info['len'],
                text=info['name'][0],
                hovertext=info['label'],
                textposition='auto',
                orientation='h',
                showlegend=False
            ))
    
    
    print(range)
    
    fig.update_xaxes(range=range, row=1, col=1)
    
    fig.show(config=config)
    
    return



if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--dir', '-d', help='directory which have your log file', required=True)
    # args = parser.parse_args()
    
    data_path = './ftrace_parse_data.json'
    core_info_data = load_data(data_path)
    visualize_all_cores(core_info_data)