import os
import shutil
import hashlib
from datetime import datetime
import zipfile
from cryptography.fernet import Fernet

# Configuration
SOURCE_DIR = "source_data"         # Directory to back up
BACKUP_DIR = "backups"             # Where backups are saved
LOG_FILE = "logs/backup.log"       # Log file
LOG_FILE = "logs/backup.log"
KEY_FILE = "secret.key"

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
              # Generate hash and save to a hash file
            hash_value = hash_file(src_path)
            with open(os.path.join(destination, "hashes.txt"), "a") as hash_log:
                hash_log.write(f"{rel_path} {hash_value}\n")
            log_backup(f"Backed up: {src_path} -> {dest_path}")

def create_zip(source_folder, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_folder)
                zipf.write(file_path, arcname)

def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)
    return key

def load_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        return generate_key()

def encrypt_file(input_file, output_file, key):
    fernet = Fernet(key)
    with open(input_file, 'rb') as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(output_file, 'wb') as f:
        f.write(encrypted)

def hash_file(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def verify_hashes(backup_dir):
    hash_file_path = os.path.join(backup_dir, "hashes.txt")
    if not os.path.exists(hash_file_path):
        print("No hash file found.")
        return False

    with open(hash_file_path, "r") as f:
        for line in f:
            rel_path, expected_hash = line.strip().split()
            file_path = os.path.join(backup_dir, rel_path)

            if not os.path.exists(file_path):
                print(f"Missing file: {rel_path}")
                return False

            actual_hash = hash_file(file_path)
            if actual_hash != expected_hash:
                print(f"Hash mismatch: {rel_path}")
                return False

    print("All hashes verified.")
    return True

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_subdir = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(backup_subdir)

    print(f"Starting backup from '{SOURCE_DIR}' to '{backup_subdir}'...")
    copy_files(SOURCE_DIR, backup_subdir)
    print("Backup complete.")

    # Compress backup folder
    zip_path = f"{backup_subdir}.zip"
    create_zip(backup_subdir, zip_path)
    print(f"Compressed backup to '{zip_path}'")

    # Encrypt the zip file
    key = load_key()
    encrypted_path = f"{zip_path}.enc"
    encrypt_file(zip_path, encrypted_path, key)
    print(f"Encrypted backup saved to '{encrypted_path}'")

    # Optional cleanup
    shutil.rmtree(backup_subdir)
    os.remove(zip_path)

    print("All done. Details saved in log.")