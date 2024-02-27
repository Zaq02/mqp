import matplotlib.pyplot as plt
import numpy as np
import json
import re
import sys
import os

#gets ridd of offset if values don't align on graphs
def apply_offset(values, offset, threshold):
    if values and values[0] > threshold:
        return [value - offset for value in values]
    else:
        return values

def get_first_float(input_string):
    pattern = r'([-+]?\d*\.\d+|\d+)'
    matches = re.findall(pattern, input_string)

    # Get the first float from the entire text
    return float(matches[0]) if matches else None

def get_mouse_times(input_string, keyword="Mouse"):
    pattern = r'\[([^\]]*)\]' + keyword
    matches = re.findall(pattern, input_string)

    # Get floats from lines that include the keyword
    return [float(token) for token in matches]

def get_keystroke_times(input_string, keyword="Mouse"):
    mouse_pattern = r'\[([^\]]*)\]' + keyword
    mouse_matches = re.findall(mouse_pattern, input_string)
    mouse_tokens = [float(token) for token in mouse_matches]

    pattern = r'\[([^]]*(?<!' + re.escape(keyword) + r')[^]]*)\]'
    keystroke_matches = re.findall(pattern, input_string)
    # Get floats from lines that do not include the keyword
    keystroke_tokens = [float(token.strip()) for token in keystroke_matches]

    # Remove mouse_tokens from keystroke_tokens
    keystroke_tokens = [token for token in keystroke_tokens if token not in mouse_tokens]

    return keystroke_tokens


def process_generic_activity(activity_data, temp_epoch, offset):
    return [float(call.get("time")) - temp_epoch + offset for item in activity_data for call in item.get("calls", [])]

#def process_file_system_activity(file_data, temp_epoch, offset):
#    return [float(call.get("time")) - temp_epoch + offset for file in file_data for call in file.get("calls", []) if call.get("category") == "file"]

def process_file_system_create_activity(file_data, temp_epoch, offset):
    return [float(call.get("time")) - temp_epoch + offset for file in file_data for call in file.get("calls", []) if call.get("category") == "file" and call.get("api") == "NtCreateFile"]

def process_file_system_read_activity(file_data, temp_epoch, offset):
    return [float(call.get("time")) - temp_epoch + offset for file in file_data for call in file.get("calls", []) if call.get("category") == "file" and call.get("api") == "NtReadFile"]

def process_file_system_open_activity(file_data, temp_epoch, offset):
    return [float(call.get("time")) - temp_epoch + offset for file in file_data for call in file.get("calls", []) if call.get("category") == "file" and call.get("api") == "NtOpenFile"]

def process_file_system_close_activity(file_data, temp_epoch, offset):
    return [float(call.get("time")) - temp_epoch + offset for file in file_data for call in file.get("calls", []) if call.get("category") == "file" and call.get("api") == "NtClose"]

def process_tor2web_connections(file_data, temp_epoch, offset):
    return [float(call.get("time")) - temp_epoch + offset for file in file_data for call in file.get("calls", []) if "buffer" in call["arguments"] and "tor2web" in call["arguments"]["buffer"]]

def process_udp_connections(udp_data, temp_epoch):
    return [float(item.get("time")) for item in udp_data]

def process_tcp_connections(tcp_data, temp_epoch):
    return [float(item.get("time")) for item in tcp_data]


def plot_event_times(event_times_list, graph_names, graph_title, time_interval=5):
    fig, axs = plt.subplots(len(event_times_list), 1, sharex=True, sharey=False, figsize=(8, 4 * len(event_times_list)))

    end_time = max(start for event_times in event_times_list for start in event_times)
    end_time = int(np.ceil(end_time / time_interval)) * time_interval

    colors = plt.cm.viridis(np.linspace(0, 1, len(event_times_list)))

    for i, (event_times, ax, color) in enumerate(zip(event_times_list, axs, colors)):
        flattened_times = [start for start in event_times]

        if flattened_times:
            all_intervals = set(range(0, end_time + 1, time_interval))

            events_at_interval = {interval_start: sum(1 for start in flattened_times if interval_start <= start < interval_start + time_interval) for interval_start in all_intervals}

            x_coords = [0] + sorted(events_at_interval.keys()) + [end_time]
            y_coords = [0] + [events_at_interval[time] for time in sorted(events_at_interval.keys())] + [0]

            ax.plot(x_coords, y_coords, linestyle='-', marker='', drawstyle='steps-post', color=color)

        ax.set_title(f'{graph_names[i]}', fontweight='bold')
        #ax.set_xlabel('Time (seconds)')
        fig.suptitle(graph_title, fontsize=18, fontweight='bold', x=0.55, y=0.995)
        fig.text(0.55, 0.03, 'Time (seconds)', ha='center', va='center')
        ax.set_ylabel(f'{graph_yaxes[i]}', rotation=0, labelpad=70)
        if graph_names[i] == "Keystrokes" or graph_names[i] == "Mouse Clicks":
            if not event_times:
                ax.set_yticks([])
            continue
        else:   
            ax.set_yticks([])

        ax.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Get folder name from command line arguments
    if len(sys.argv) != 2:
        print("Usage: python3 monitor.py <folder_name>")
        sys.exit(1)

    folder_name = sys.argv[1]
    graph_title = sys.argv[1]

    # Construct file path for the specified folder
    current_directory = os.getcwd()
    results_folder_path = os.path.join(current_directory, "Results", folder_name)
    json_log_file_path = os.path.join(results_folder_path, "output.json")

    # Load data from the specified "output.json" file
    with open(json_log_file_path, 'r') as input_file:
        input_data = json.load(input_file)

    temp_epoch = input_data.get("Cuckoo", {}).get("behavior", {}).get("generic", [{}])[0].get("first_seen", None)
    offset = 427 #value to ensure alignment on graphs
    threshold = 400 #value to remove offset if not aligned on graphs

    #starting_time: Time to subtract from mouse/keystrokes epoch to start values at 0 on graph
    starting_time = get_first_float(input_data.get("KeyLogger", "")) 
    keylog_mouse_events = get_mouse_times(input_data.get("KeyLogger", ""))
    keylog_keystrokes = get_keystroke_times(input_data.get("KeyLogger", ""))

    udp_connections = process_udp_connections(input_data.get("Cuckoo", {}).get("network", {}).get("udp", []), temp_epoch)
    tcp_connections = process_tcp_connections(input_data.get("Cuckoo", {}).get("network", {}).get("tcp", []), temp_epoch)
    tor2web_connections = apply_offset(process_tor2web_connections(input_data.get("Cuckoo", {}).get("behavior", {}).get("processes", []), temp_epoch, offset), offset, threshold)

    process_activity = apply_offset(process_generic_activity(input_data.get("Cuckoo", {}).get("behavior", {}).get("processes", []), temp_epoch, offset), offset, threshold)
    #file_system_activity = process_file_system_activity(input_data.get("Cuckoo", {}).get("behavior", {}).get("processes", []), temp_epoch, offset)
    file_system_create_activity = apply_offset(process_file_system_create_activity(input_data.get("Cuckoo", {}).get("behavior", {}).get("processes", []), temp_epoch, offset), offset, threshold)    
    file_system_read_activity = apply_offset(process_file_system_read_activity(input_data.get("Cuckoo", {}).get("behavior", {}).get("processes", []), temp_epoch, offset), offset, threshold)
    file_system_open_activity = apply_offset(process_file_system_open_activity(input_data.get("Cuckoo", {}).get("behavior", {}).get("processes", []), temp_epoch, offset), offset, threshold)
    file_system_close_activity = apply_offset(process_file_system_close_activity(input_data.get("Cuckoo", {}).get("behavior", {}).get("processes", []), temp_epoch, offset), offset, threshold)
    
    print("create:")
    print(file_system_create_activity)
    print("Read:")
    print(file_system_read_activity)
    print("open:")
    print(file_system_open_activity)
    print("close:")
    print(file_system_close_activity)
    print("tor2web:")
    print(tor2web_connections)

    user_activity_keystrokes = [(start - starting_time) for start in keylog_keystrokes]
    user_activity_mouse_clicks = [(start - starting_time) for start in keylog_mouse_events]
    
    
    event_times_list = [udp_connections, tcp_connections, tor2web_connections, process_activity, file_system_create_activity, file_system_read_activity, file_system_open_activity, file_system_close_activity]
    
    graph_names = ["UDP Connections", "TCP Connections", "Tor2Web Connections", "Processes", "Files Created", "Files Read","Files Opened", "Files Closed"]
    graph_yaxes = ["# of Connections", "# of Connections", "# of Connections", "# of Active Processes", "Files Created", "Files Read", "Files Opened", "Files Closed"]
    

    # Get rid of empty graphs
    non_empty_event_times = [times for times in event_times_list if times]
    non_empty_graph_names = [name for times, name in zip(event_times_list, graph_names) if times]
    non_empty_graph_yaxes = [yaxis for yaxis, times in zip(graph_yaxes, event_times_list) if times]
    graph_yaxes = non_empty_graph_yaxes
    
    final_event_times = non_empty_event_times.append(user_activity_keystrokes)
    final_event_times = non_empty_event_times.append(user_activity_mouse_clicks)
    final_graph_names = non_empty_graph_names.append("Keystrokes")
    final_graph_names = non_empty_graph_names.append("Mouse Clicks")
    final_graph_yaxes = graph_yaxes.append("# of Keystrokes")
    final_graph_yaxes = graph_yaxes.append("# of Mouse Clicks")


    plot_event_times(non_empty_event_times, non_empty_graph_names, graph_title, time_interval=1)

    #Pictures To Come Back To:
    #Golden Eyes, 

    #Cerber: process (?), create -396, read +9, open +8
    #WannaCrypt: process +154, create +154, read +154, open +154, tor2web +100
    #GhostCrypter: process +45, create +45, read +45, open +45, tor2web +45

