import os
import shutil
from datetime import datetime

# Configuration
SOURCE_DIR = "source_data"         # Directory to back up
BACKUP_DIR = "backups"             # Where backups are saved
LOG_FILE = "logs/backup.log"       # Log file

# Ensure directories exist
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

def log_backup(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log:
        log.write(f"[{timestamp}] {message}\n")

def copy_files(source, destination):
    for root, dirs, files in os.walk(source):
        for file in files:
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, source)
            dest_path = os.path.join(destination, rel_path)
            
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(src_path, dest_path)
            log_backup(f"Backed up: {src_path} -> {dest_path}")

if __name__ == "__main__":
    backup_subdir = os.path.join(BACKUP_DIR, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(backup_subdir)
    
    print(f"Starting backup from '{SOURCE_DIR}' to '{backup_subdir}'...")
    copy_files(SOURCE_DIR, backup_subdir)
    print("Backup complete. Details saved in log.")