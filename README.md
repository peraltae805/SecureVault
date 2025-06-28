# SecureVault

SecureVault is a Python-based automated backup and recovery tool that emphasizes security, encryption, and integrity verification. It helps safeguard important data through encrypted, verifiable backups—scheduled or on-demand.

# Features

Automated daily backups (via scheduling)

AES encryption using Fernet (symmetric encryption)

SHA-256 hashing for file integrity

Zip compression for efficient storage

Restoration from encrypted backups

Simulated tests for missing or corrupted files

Logging for both backup and restore processes

# Project Structure 
```bash
.
├── source_data/          # Your original data to back up
├── backups/              # Encrypted backups saved here
├── logs/                 # Contains backup.log and restore.log
├── secret.key            # Encryption key (auto-generated if missing)
└── securevault.py        # Main script
```

### Install dependencies
```bash
pip install cryptography schedule
```

### Restore from backup
``` bash
python securevault.py --restore backups/YYYYMMDD_HHMMSS.zip.enc --output restored_data
```

### Enable scheduled backups (daily at 12:00)
```bash
python securevault.py --schedule
```
Press Ctrl + C to shopt scheduler. 

### Optional Test Modes
```bash
python securevault.py --test-missing path/to/backup.enc
python securevault.py --test-corrupt path/to/backup.enc
```

### Key Management
A key file (secret.key) is created automatically if missing.

You can also load the key via an environment variable:
```bash
export SECUREVAULT_KEY="your_base64_encoded_key"
```
### Logs
    Backup logs: logs/backup.log

    Restore logs: logs/restore.log

Each step (copy, compression, encryption, restore) is timestamped for auditing and troubleshooting.

### Integrity Verification 
Each file is hashed during backup.

After decryption and extraction, hashes are rechecked.

The process will fail and log issues if files are tampered with or missing.

### Requirments
Python 3.6+
Libraries: cryptography, schedule
