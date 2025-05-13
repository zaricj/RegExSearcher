import cProfile
import re
import csv
from tqdm import tqdm
import os
from multiprocessing import Pool


def extract_info_from_line(line, date):
    """Extracts time, job numbers, profile names, filenames, and filesizes from a log file line.

    Args:
        line: A single line from the log file.

    Returns:
        A list containing the extracted information if found, otherwise None.
    """
    # Patterns for extracting information
    time_pattern = r"\b(\d{2}:\d{2}:\d{2})\b"
    job_number_pattern = r"Job:\s+((?:\d+|GENERAL))"
    profilename_pattern = r"\[(.*?)\)]"
    sys_par_id_group_pattern = r"\] (.*?):.*?Parent job ID is (\d+)"
    filesize_pattern = r"length=(\d+),"

    # Extract information using regular expressions
    time_match = re.search(time_pattern, line)
    job_number_match = re.search(job_number_pattern, line)
    profilename_match = re.search(profilename_pattern, line)
    sys_par_id_group_match = re.search(sys_par_id_group_pattern, line)

    if time_match and profilename_match and sys_par_id_group_match and job_number_match:
        time = time_match.group(1)
        time = f"{date} {time}"
        job_numbers = job_number_match.group(1)
        profilenames = profilename_match.group(1)
        system_name, parent_id = sys_par_id_group_match.group(1), sys_par_id_group_match.group(2)
        return [time, job_numbers, profilenames, system_name, parent_id]
    else:
        return None


def process_file(filepath):
    """Processes a single log file.

    Args:
        filepath: Path to the log file.

    Returns:
        A list containing the extracted information from the log file.
    """
    matching_lines = []
    filename = os.path.basename(filepath)[:10] # If filename is like 13_05_2025_message.log then 13_05_2025 will be outputted only

    with open(filepath, "r", encoding="utf-8") as log_file:
        total_lines = sum(1 for _ in log_file)  # Get total lines in the file
        log_file.seek(0)  # Reset file pointer to start

        # Initialize tqdm progress bar for each line
        progress_bar = tqdm(total=total_lines, desc=f"Processing {os.path.basename(filepath)}", unit=" lines")

        for line in log_file:
            # Extract information from the line
            extracted_info = extract_info_from_line(line, filename)
            if extracted_info:
                matching_lines.append(extracted_info)
            progress_bar.update(1)  # Update progress bar for each line processed

        progress_bar.close()

    return matching_lines


def extract_and_write_to_csv(filepath, output_file_csv="extracted_info.csv"):
    """Extracts job numbers, profile names, filenames, and filesizes from log files and writes them to a CSV.

    Args: 
        filepath: The path to the log file or directory containing log files.
        output_file_csv (optional): The name of the output CSV file (defaults to "extracted_info.csv").
    """
    
    if not os.path.exists(output_file_csv):
        os.makedirs(os.path.dirname(output_file_csv), exist_ok=True)
        print("Directory did not exist, created it. ")

    print("Starting app, please wait...")
    
    if os.path.isfile(filepath):
        files = [filepath]
    elif os.path.isdir(filepath):
        files = [os.path.join(filepath, f) for f in os.listdir(filepath) if f.endswith("_message.log")]
    else:
        print("Invalid filepath.")
        return

    data = []

    for file in tqdm(files, desc="Processing Files"):
        data.extend(process_file(file))
        # Sort data

    try:
        with open(output_file_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Time", "Job Number", "Profile Name", "System Name", "Parent Job ID"])  # Header row
            writer.writerows(data)
        print(f"Data has been written to {output_file_csv}")
        print(f"Total Matches: {len(data)}")
    except Exception as e:
        print("Error writing to CSV:", e)

if __name__ == "__main__":
    # Profile the main function
    #profiler = cProfile.Profile()
    #profiler.enable()

    # Run main function, change log file path accordingly
    filepath = r"C:\Users\ZaricJ\Downloads\NESIST02 DataWizard Logs"
    output_csv = r"C:\Users\ZaricJ\Downloads\NESIST02 DataWizard Logs\CSV\results.csv"

    extract_and_write_to_csv(filepath, output_csv)

    #profiler.disable()
    #profiler.print_stats()

