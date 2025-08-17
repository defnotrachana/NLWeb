import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCHED_DIR = r"C:/Users/RACHANAA/OneDrive - Virtusa/Desktop/NLWeb/NLWeb/code/data"
WATCHED_FILE = "job_postings_transformed.jsonl"

# Path to your Qdrant local db folder (adjust as needed)
QDRANT_DB_PATH = r"C:/Users/RACHANAA/OneDrive - Virtusa/Desktop/NLWeb/NLWeb/data/db"
LOCK_FILE_NAME = ".lock"  # or check for 'LOCK', adjust as per what you see in your folder

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith(WATCHED_FILE):
            print(f"{WATCHED_FILE} has been modified. Preparing to run ingestion...")

            # 1. Remove lock file if it exists
            lock_file_path = os.path.join(QDRANT_DB_PATH, LOCK_FILE_NAME)
            if os.path.exists(lock_file_path):
                try:
                    os.remove(lock_file_path)
                    print(f"Deleted lock file at: {lock_file_path}")
                except Exception as e:
                    print(f"Failed to delete lock file: {e}")

            # 2. Run your ingestion command automatically with input 'y' to avoid prompt
            cmd = [
                "python", "-m", "tools.db_load",
                f"{WATCHED_DIR}/{WATCHED_FILE}",
                "careerportal",
                # 
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, input="y\n", check=True)
                print("Ingestion Output:\n", result.stdout)
                if result.stderr:
                    print("Ingestion Errors:\n", result.stderr)
            except subprocess.CalledProcessError as e:
                print(f"Ingestion subprocess failed with code {e.returncode}")
                print(f"Output: {e.output}")
                print(f"Error: {e.stderr}")
            except Exception as e:
                print(f"Exception running ingestion: {e}")

if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCHED_DIR, recursive=False)
    observer.start()
    print(f"Watching for changes in {WATCHED_DIR}/{WATCHED_FILE}...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
