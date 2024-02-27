import json
import os
import sys

def format_to_log(folder_name):
    # Construct file paths based on user input
    current_directory = os.getcwd()
    results_folder_path = os.path.join(current_directory, "Results", folder_name)
    json_file_path = os.path.join(results_folder_path, "report.json")
    text_file_path = os.path.join(results_folder_path, "ubuntuLogfile.txt")
    json_log_file_path = os.path.join(results_folder_path, "output.json")

    # Read JSON data
    with open(json_file_path, 'r') as json_file:
        json_data = json.load(json_file)

    # Check if text file exists before reading
    if os.path.exists(text_file_path):
        with open(text_file_path, 'r') as text_file:
            text_data = text_file.read()
    else:
        text_data = ""

    # Combine JSON and text data into a log format
    log_content = {
        "Cuckoo": json_data,
        "KeyLogger": text_data
    }

    # Write the formatted data to the JSON log file in the Results folder
    with open(json_log_file_path, 'w') as json_log_file:
        json.dump(log_content, json_log_file, indent=2)

if __name__ == "__main__":
    # Get folder name from command line arguments
    if len(sys.argv) != 2:
        print("Usage: python3 createLog.py <folder_name>")
        sys.exit(1)

    folder_name = sys.argv[1]

    # Call the function to format data and create the JSON log file
    format_to_log(folder_name)

    print(f"JSON log file created at Results/{folder_name}/output.json.")
