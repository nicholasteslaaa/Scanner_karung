import subprocess
import platform

def launch_scripts(script_list):
    current_os = platform.system()
    
    for script in script_list:
        if current_os == "Windows":
            # Windows command
            subprocess.Popen(f'start cmd /k python {script}', shell=True)
        
        elif current_os == "Linux":
            # Raspberry Pi / Linux command
            subprocess.Popen(['lxterminal', '-e', f'bash -c "python3 {script}; exec bash"'])
            
        else:
            print(f"Unsupported OS: {current_os}")

# Usage
my_files = ["webcam_manager.py", "API_master.py", "video_capture.py"]
launch_scripts(my_files)