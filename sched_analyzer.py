import numpy as np
from parse import compile
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
import json

# TODO
file_path = "/home/bkpark/workspace/ftrace_sched_analyzer/ftrace_log.txt"
CPU_NUM = 12
process_name = ["op_global_plann",
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

# 
TIME = 0
PREV_COMM = 1
PREV_PID = 2
PREV_PRIO = 3
PREV_STAT = 4
NEXT_COMM = 5
NEXT_PID = 6
NEXT_PRIO = 7

#
start_time = 0.0
end_time = 0.0

def parse_ftrace_log(file):
    func_pattern = compile("{}[{}] {}  {}: {}: {}")
    sched_switch_pattern = compile("{}[{}] {}  {}: {}: prev_comm={} prev_pid={} prev_prio={} prev_state={} ==> next_comm={} next_pid={} next_prio={}")

    per_cpu_info = {}
    
    for i in range(CPU_NUM):
        per_cpu_info['cpu'+str(i)] = []

    start_time = 0
    update_start_time = False
    while True:
        line = file.readline()
        if not line:
            break
        
        result = func_pattern.parse(line)
        
        if result != None:
            if result[4] == 'sched_switch':
                sched_parse_result = sched_switch_pattern.parse(line)
                
                if not update_start_time:
                    start_time = float(sched_parse_result[3])
                    update_start_time = True

                per_cpu_info['cpu' + str(int(sched_parse_result[1]))].append((float(sched_parse_result[3])-start_time, sched_parse_result[5], int(sched_parse_result[6]),
                                                                              int(sched_parse_result[7]), sched_parse_result[8], sched_parse_result[9],
                                                                              int(sched_parse_result[10]), int(sched_parse_result[11])))

    return per_cpu_info

def update_per_process_info(cpu_info):
    per_cpu_info, per_cpu_start_info = {}, {}
    per_process_info, per_process_start_info = {}, {}

    for i in range(len(process_name)):
        per_process_info[process_name[i]] = []
        # (is_start, start_time, pid)
        per_process_start_info[process_name[i]] = [False, 0.0, 0]
    
    for i in range(CPU_NUM):
        per_cpu_info['cpu'+str(i)] = per_process_info
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
                            per_cpu_info['cpu' + str(i)][process_name[k]].append((per_cpu_start_info['cpu'+str(i)][process_name[k]][2],
                                                                                  per_cpu_start_info['cpu'+str(i)][process_name[k]][1], cpu_info['cpu'+str(i)][j][TIME]))
                
                if max_time < cpu_info['cpu'+str(i)][j][TIME]:
                    max_time = cpu_info['cpu'+str(i)][j][TIME]

    return per_cpu_info, max_time

# WORKING ON
def sched_display(per_cpu_info, max_time):
    end_time = max_time
    scale = 1000

    fig, ax = plt.subplots()
    plt.subplots_adjust(left=0.25, bottom=0.25)

    t = np.arange(0.0, 1.0, 0.001)
    a0 = 5
    f0 = 3
    delta_f = 5.0
    s = a0 * np.sin(2 * np.pi * f0 * t)
    l, = plt.plot(t, s, lw=2)
    
    axcolor = 'lightgoldenrodyellow'
    axStartTime = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor=axcolor)
    axEndTime = plt.axes([0.25, 0.15, 0.65, 0.03], facecolor=axcolor)

    sStartTime = Slider(axStartTime, "start time (ms)", 0.0, max_time * scale, valinit=start_time * scale, valstep=0.001)
    sEndTime = Slider(axEndTime, "end time (ms)", 0.0, max_time * scale, valinit=end_time * scale, valstep=0.001)

    def update(val):
        start_time = sStartTime.val
        end_time = sEndTime.val
        print(end_time)

    sStartTime.on_changed(update)
    sEndTime.on_changed(update)

    plt.show()

if __name__ == "__main__":
    file = open(file_path, "r")
    
    per_cpu_info = parse_ftrace_log(file)
    per_cpu_info, max_time = update_per_process_info(per_cpu_info)
    
    with open("ftrace_parse_data.json", "w") as json_file:
        json.dump(per_cpu_info, json_file, indent=4)

    # sched_display(per_cpu_info, max_time)



    
    
    