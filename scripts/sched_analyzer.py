import matplotlib
import numpy as np
from parse import compile
import copy
import json
import os

############### TODO ###############
# core number of your computer
CPU_NUM = 4
# analyze autoware node only
ONLY_AUTOWARE = False
####################################

# 
TIME = 0
PREV_COMM = 1
PREV_PID = 2
PREV_PRIO = 3
PREV_STAT = 4
NEXT_COMM = 5
NEXT_PID = 6
NEXT_PRIO = 7

def parse_ftrace_log(file, process_name):
    func_pattern = compile("{}[{}] {} {}: {}: {}")
    sched_switch_pattern = compile("{}[{}] {} {}: {}: prev_comm={} prev_pid={} prev_prio={} prev_state={} ==> next_comm={} next_pid={} next_prio={}")

    per_cpu_info = {}
    
    for i in range(CPU_NUM):
        per_cpu_info['cpu'+str(i)] = []

    if not ONLY_AUTOWARE:
        process_name = []

    while True:
        line = file.readline()
        if not line:
            break
        
        result = func_pattern.parse(line)
        
        if result != None:
            if result[4] == 'sched_switch':
                sched_parse_result = sched_switch_pattern.parse(line)

                per_cpu_info['cpu' + str(int(sched_parse_result[1]))].append((float(sched_parse_result[3]), sched_parse_result[5], int(sched_parse_result[6]),
                                                                              int(sched_parse_result[7]), sched_parse_result[8], sched_parse_result[9],
                                                                              int(sched_parse_result[10]), int(sched_parse_result[11])))

                if not ONLY_AUTOWARE:
                    already_exist = False
                    for i in range(len(process_name)):
                        if process_name[i] == sched_parse_result[5]:
                            already_exist = True
                    if not already_exist:
                        if not sched_parse_result[5][0:7] == "swapper":
                            process_name.append(sched_parse_result[5])

    return per_cpu_info, process_name

def update_per_process_info(cpu_info, process_name):
    per_cpu_info, per_cpu_start_info = {}, {}
    per_process_info, per_process_start_info = {}, {}

    for i in range(len(process_name)):
        per_process_info[process_name[i]] = []
        # (is_start, start_time, pid)
        per_process_start_info[process_name[i]] = [False, 0.0, 0]

    for i in range(CPU_NUM):
        per_cpu_info['cpu'+str(i)] = copy.deepcopy(per_process_info)
        per_cpu_start_info['cpu'+str(i)] = per_process_start_info

    max_time = 0.0
    for i in range(CPU_NUM):
        for j in range(len(cpu_info['cpu'+str(i)])):
            for k in range(len(process_name)):
                if cpu_info['cpu'+str(i)][j][NEXT_COMM] == process_name[k]:
                    per_cpu_start_info['cpu'+str(i)][process_name[k]][0] = True
                    per_cpu_start_info['cpu'+str(i)][process_name[k]][1] = cpu_info['cpu'+str(i)][j][TIME]
                    per_cpu_start_info['cpu'+str(i)][process_name[k]][2] = cpu_info['cpu'+str(i)][j][NEXT_PID]

                if cpu_info['cpu'+str(i)][j][PREV_COMM] == process_name[k]:
                    if cpu_info['cpu'+str(i)][j][PREV_PID] == per_cpu_start_info['cpu'+str(i)][process_name[k]][2]:
                        if per_cpu_start_info['cpu'+str(i)][process_name[k]][0]:
                            per_cpu_start_info['cpu'+str(i)][process_name[k]][0] = False
                            
                            process_info = {}
                            process_info['PID'] = per_cpu_start_info['cpu'+str(i)][process_name[k]][2]
                            process_info['StartTime'] = per_cpu_start_info['cpu'+str(i)][process_name[k]][1]
                            process_info['EndTime'] = cpu_info['cpu'+str(i)][j][TIME]

                            per_cpu_info['cpu'+str(i)][process_name[k]].append(process_info)
                
                if max_time < cpu_info['cpu'+str(i)][j][TIME]:
                    max_time = cpu_info['cpu'+str(i)][j][TIME]

    return per_cpu_info, max_time

def filtering_process_info(per_cpu_info):
    for i in range(CPU_NUM):
        for j in range(len(process_name)):
            if len(per_cpu_info['cpu'+str(i)][process_name[j]]) == 0:
                per_cpu_info['cpu'+str(i)].pop(process_name[j])
    
    return per_cpu_info

def create_filtering_option(process_name):
    filtering_option = {}
    for i in range(len(process_name)):
        filtering_option[process_name[i]] = True
    return filtering_option

if __name__ == "__main__":
    # matplotlib.use("TkAgg")

    process_name = [
                "republish",
                "op_global_plann",
                "op_trajectory_g",
                "op_trajectory_e",
                "op_behavior_sel",
                "ray_ground_filt",
                "lidar_euclidean",
                "imm_ukf_pda",
                "op_motion_predi",
                "lidar_republish",
                "voxel_grid_filt",
                "ndt_matching",
                "relay",
                "rubis_pose_rela",
                "pure_pursuit",
                "twist_filter",
                "twist_gate"]

    file_path = os.path.dirname(os.path.realpath(__file__))[0:-7]

    file = open(file_path + "/sample/ftrace_log.txt", "r")

    per_cpu_info, process_name = parse_ftrace_log(file ,process_name)
    per_cpu_info, max_time = update_per_process_info(per_cpu_info, process_name)
    per_cpu_info = filtering_process_info(per_cpu_info)

    with open(file_path + "/data/sample.json", "w") as json_file:
        json.dump(per_cpu_info, json_file, indent=4)
    
    filtering_option = create_filtering_option(process_name)
    with open(file_path + "/filtering_option.json", "w") as json_file:
        json.dump(filtering_option, json_file, indent=4)
    
