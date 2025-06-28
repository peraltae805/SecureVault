from doctest import testmod # Ensure this is the first import
import os # Import necessary libraries
import shutil # For file operations
import hashlib # For hashing files
from datetime import datetime # For timestamps
import zipfile # For creating zip files
import schedule # For scheduling backups
import time # For time management
from cryptography.fernet import Fernet # For encryption and decryption
import argparse # For command line argument parsing
import sys # For system operations

# Configuration
SOURCE_DIR = "source_data"         # Directory to back up
BACKUP_DIR = "backups"             # Where backups are saved
LOG_FILE = "logs/backup.log"       # Log file
RESTORE_LOG = "logs/restore.log"  # Restore log file
KEY_FILE = "secret.key"          # Encryption key file

# Ensure directories exist
os.makedirs(BACKUP_DIR, exist_ok=True) # Ensure backup directory exists
os.makedirs("logs", exist_ok=True) # Ensure logs directory exists

# Logging function
def log_backup(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log:
        log.write(f"[{timestamp}] {message}\n")

# Logging function for restore operations
def log_restore(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/restore.log", "a") as log:
        log.write(f"[{timestamp}] {message}\n")

# Hashing function for file integrity
def hash_file(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# File Copy with Hashing and Logging        
def copy_files(source, destination):
    hash_log_path = os.path.join(destination, "hashes", "hashes.txt")
    os.makedirs(os.path.dirname(hash_log_path), exist_ok=True)

    for root, dirs, files in os.walk(source):
        for file in files:
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, source)
            dest_path = os.path.join(destination, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(src_path, dest_path)

            # Generate hash and save to a hash file
            hash_value = hash_file(src_path)
            with open(hash_log_path, "a") as hash_log:
                hash_log.write(f"{rel_path} {hash_value}\n")
            log_backup(f"Backed up: {src_path} -> {dest_path}")

#compression
def create_zip(source_folder, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_folder)
                zipf.write(file_path, arcname)

# Encryption Key Management
def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)
    return key

# Load encryption key from environment variable or file
def load_key():
    key = os.getenv('SECUREVAULT_KEY')
    if key:
        return key.encode()  # Convert string to bytes
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        return generate_key()

# Encrypt/Decrypt Files
def encrypt_file(input_file, output_file, key):
    try:
        fernet = Fernet(key)
        with open(input_file, 'rb') as f:
            data = f.read()
        encrypted = fernet.encrypt(data)
        with open(output_file, 'wb') as f:
            f.write(encrypted)
    except Exception as e:
        log_backup(f"Encryption failed: {e}")

# Decrypt File
def decrypt_file(encrypted_file, decrypted_zip):
    try:
        key = load_key()
        fernet = Fernet(key)
        with open(encrypted_file, 'rb') as ef:
            encrypted_data = ef.read()
        decrypted_data = fernet.decrypt(encrypted_data)
        with open(decrypted_zip, 'wb') as df:
             df.write(decrypted_data)
        log_restore(f"Decrypted: {encrypted_file} -> {decrypted_zip}")
    except Exception as e:
        log_restore(f"Decryption failed: {e}")
        raise

#Verify Hashes
def verify_hashes(backup_dir):
    hash_file_path = os.path.join(backup_dir, "hashes", "hashes.txt")
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

# Verify extracted hashes during restore
def verify_extracted_hashes(extracted_dir):
    hash_file_path = os.path.join(extracted_dir, "hashes" "hashes.txt")
    if not os.path.exists(hash_file_path):
        log_restore("No hash file found.")
        return False
    with open(hash_file_path, "r") as f:
        for line in f:
            rel_path, expected_hash = line.strip().split()
            file_path = os.path.join(extracted_dir, rel_path)
            if not os.path.exists(file_path):
                log_restore(f"Missing file: {rel_path}")
                return False
            actual_hash = hash_file(file_path)
            if actual_hash != expected_hash:
                log_restore(f"Hash mismatch: {rel_path}")
                return False
    log_restore("All hashes verified successfully.")
    return True

# Extract and restore
def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        log_restore(f"Extracted: {zip_path} -> {extract_to}")
    except zipfile.BadZipFile as e:
        log_restore(f"Extraction failed: {e}")
        raise
# Restore files from extracted directory
def restore_files(extracted_dir, restore_to):
    for root, dirs, files in os.walk(extracted_dir):
        for file in files:
            if file == "hashes.txt":
                continue
            src = os.path.join(root, file)
            rel_path = os.path.relpath(src, extracted_dir)
            dest = os.path.join(restore_to, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                shutil.copy2(src, dest)
                log_restore(f"Restored: {src} -> {dest}")
            except Exception as e:
                log_restore(f"Failed to restore {src}: {e}")

# Restore Function
def restore_backup(encrypted_backup_path, restore_to="restored_data"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_zip = f"temp_restore_{timestamp}.zip"
    temp_dir = f"temp_restore_{timestamp}_dir"
    try:
        decrypt_file(encrypted_backup_path, temp_zip)
        os.makedirs(temp_dir, exist_ok=True)
        extract_zip(temp_zip, temp_dir)
        
        # Simulated test cases
        if testmod == "missing":
            test_file = os.path.join(temp_dir, os.listdir(temp_dir)[0])
            if os.path.isfile(test_file):
                os.remove(test_file)
                log_restore("TEST: Simulated missing file.")

         # Simulated test case for corrupted hash
        if testmod == "corrupt":
            hash_file_path = os.path.join(temp_dir, "hashes", "hashes.txt")
            with open(hash_file_path, "a") as f:
                f.write("tampered.txt deadbeef\n")
            log_restore("TEST: Simulated corrupted hash.")

        # Verify hashes after extraction
        if verify_extracted_hashes(temp_dir):
            os.makedirs(restore_to, exist_ok=True)
            restore_files(temp_dir, restore_to)
            log_restore("Restore completed successfully.")
            sys.exit(0) # Exit with success code
        else:
            log_restore("Restore aborted: hash verification failed.")
            sys.exit(1) # Exit with failure code
    except Exception as e:
        log_restore(f"Restore failed: {e}")
        sys.exit(1) # Exit with failure code
    finally:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

# Scheduled Backup Function
def scheduled_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
    backup_subdir = os.path.join(BACKUP_DIR, timestamp) 
    os.makedirs(backup_subdir) # Ensure backup directory exists
    log_backup(f"Starting backup: {SOURCE_DIR} -> {backup_subdir}") 
    copy_files(SOURCE_DIR, backup_subdir) 
    log_backup("File copy complete.")

    # Create a zip archive of the backup directory
    zip_path = f"{backup_subdir}.zip" 
    create_zip(backup_subdir, zip_path) 
    log_backup(f"Compressed to: {zip_path}") 
    
   # Encrypt the zip file
    key = load_key() 
    encrypted_path = f"{zip_path}.enc"
    encrypt_file(zip_path, encrypted_path, key) 
    log_backup(f"Encrypted backup saved to: {encrypted_path}") 
# Verify hashes after backup
    if verify_hashes(backup_subdir): 
        log_backup("Hash verification successful.") 
    else:
        log_backup("Hash verification failed.") 

    shutil.rmtree(backup_subdir)
    os.remove(zip_path)
    log_backup("Backup process completed.\n") 

# Main function to handle command line arguments
def main():
    parser = argparse.ArgumentParser(description="SecureVault Backup/Restore Tool") 
    parser.add_argument("--backup", action="store_true", help="Perform a backup now") 
    parser.add_argument("--restore", metavar="FILE", help="Path to encrypted backup (.enc)") 
    parser.add_argument("--output", metavar="DIR", default="restored_data", help="Restore destination directory") 
    parser.add_argument("--schedule", action="store_true", help="Run backup scheduler (daily at 12:00)") 
    parser.add_argument("--test-missing", metavar="FILE", help="Simulate missing file during restore")
    parser.add_argument("--test-corrupt", metavar="FILE", help="Simulate bad checksum during restore")
    args = parser.parse_args() 

# Check if the key is set in the environment variable
    if args.backup:
        scheduled_backup()
    elif args.restore:
        restore_backup(args.restore, args.output)
    elif args.test_missing:
        restore_backup(args.test_missing, args.output, test_mode="missing")
    elif args.test_corrupt:
        restore_backup(args.test_corrupt, args.output, test_mode="corrupt")
    elif args.schedule:
        schedule.every().day.at("12:00").do(scheduled_backup)
        print("Scheduler started. Press Ctrl+C to stop.")
        try: 
            while True: 
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("Scheduler stopped.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()