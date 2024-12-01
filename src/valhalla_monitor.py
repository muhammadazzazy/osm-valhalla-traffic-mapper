import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileClosedEvent
import logging
import os
import sys
from glob import glob
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def find_valhalla_service_pid():
    """Find the PID of the running valhalla_service process."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'valhalla_service' or (
                proc.info['cmdline'] and 'valhalla_service' in proc.info['cmdline'][0]
            ):
                return proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def manage_valhalla_service(valhalla_build_dir):
    """Start or restart the valhalla_service."""
    service_path = os.path.join(valhalla_build_dir, "valhalla_service")
    config_path = os.path.join(valhalla_build_dir, "valhalla.json")
    
    # Check if service is running
    pid = find_valhalla_service_pid()
    
    if pid:
        # Stop existing service
        logging.info(f"Stopping existing valhalla_service (PID: {pid})")
        try:
            psutil.Process(pid).terminate()
            time.sleep(2)  # Give it time to shut down
            if psutil.pid_exists(pid):
                psutil.Process(pid).kill()  # Force kill if still running
        except psutil.NoSuchProcess:
            pass
    
    # Start new service instance
    try:
        logging.info("Starting valhalla_service...")
        command = [service_path, config_path]
        
        # Start service in background
        subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=valhalla_build_dir
        )
        
        # Wait briefly to ensure service starts
        time.sleep(2)
        
        # Verify service is running
        if find_valhalla_service_pid():
            logging.info("valhalla_service started successfully")
        else:
            logging.error("Failed to start valhalla_service")
            
    except Exception as e:
        logging.error(f"Error managing valhalla_service: {e}")

class TrafficUpdateHandler(FileSystemEventHandler):
    def __init__(self, config_path, traffic_dir, valhalla_build_dir):
        self.config_path = config_path
        self.traffic_dir = os.path.abspath(traffic_dir)
        self.valhalla_build_dir = valhalla_build_dir
        self.valhalla_executable = os.path.join(self.valhalla_build_dir, "valhalla_add_predicted_traffic")
        self.last_run = 0
        self.cooldown = 5
        self.modified_files = set()
        self.total_files = self._count_csv_files()
        logging.info(f"Initialized handler. Expecting {self.total_files} CSV files to be modified")

    def _count_csv_files(self):
        pattern = os.path.join(self.traffic_dir, '**/**.csv')
        csv_files = glob(pattern, recursive=True)
        return len(csv_files)

    def on_closed(self, event):
        if not event.is_directory and event.src_path.endswith('.csv'):
            self.modified_files.add(event.src_path)
            remaining = self.total_files - len(self.modified_files)
            logging.info(f"File modified: {os.path.basename(event.src_path)}. Remaining files: {remaining}")

            if len(self.modified_files) >= self.total_files:
                current_time = time.time()
                if current_time - self.last_run >= self.cooldown:
                    self.last_run = current_time
                    self.update_traffic()
                    self.modified_files.clear()

    def update_traffic(self):
        try:
            logging.info("All files have been modified. Running traffic update...")
            
            # Store current directory
            original_dir = os.getcwd()
            
            try:
                # Change to build directory
                os.chdir(self.valhalla_build_dir)
                logging.info(f"Changed to directory: {self.valhalla_build_dir}")
                
                if not os.path.exists(self.valhalla_executable):
                    logging.error(f"valhalla_add_predicted_traffic not found at {self.valhalla_executable}")
                    return
                    
                command = [
                    self.valhalla_executable,
                    "-c", "valhalla.json",  # Use relative path since we're in build directory
                    "-t", "custom_files/valhalla_traffic"  # Use relative path
                ]
                
                logging.info(f"Running command: {' '.join(command)}")
                
                result = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    logging.info("Command output:")
                    for line in result.stdout.splitlines():
                        logging.info(line)
                
                logging.info("Traffic update completed successfully")
                
                # After successful traffic update, manage the service
                manage_valhalla_service(self.valhalla_build_dir)
                    
            finally:
                # Always restore original directory
                os.chdir(original_dir)
                
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running valhalla_add_predicted_traffic: {e}")
            if e.stderr:
                logging.error(f"Error output: {e.stderr}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

def main():
    valhalla_build_dir = "/home/muhammad-azzazy/Desktop/valhalla/build"
    traffic_dir = os.path.join(valhalla_build_dir, "custom_files/valhalla_traffic")
    
    # Verify paths
    if not os.path.exists(valhalla_build_dir):
        logging.error(f"Valhalla build directory not found: {valhalla_build_dir}")
        sys.exit(1)
    
    if not os.path.exists(traffic_dir):
        logging.error(f"Traffic directory not found: {traffic_dir}")
        sys.exit(1)
        
    logging.info(f"Starting traffic file monitor")
    logging.info(f"Watching directory: {traffic_dir}")
    logging.info(f"Valhalla build directory: {valhalla_build_dir}")
    
    event_handler = TrafficUpdateHandler(
        os.path.join(valhalla_build_dir, "valhalla.json"),
        traffic_dir,
        valhalla_build_dir
    )
    observer = Observer()
    observer.schedule(event_handler, traffic_dir, recursive=True)
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Monitoring stopped")
    
    observer.join()

if __name__ == "__main__":
    main()