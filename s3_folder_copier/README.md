# S3 Tools

This repository contains Python scripts for managing AWS S3 storage operations. These tools use the AWS SDK for Python (boto3) to perform common S3 tasks.

## Requirements

- Python 3.6+
- boto3 library

Install requirements:
```bash
pip install boto3
```

## Environment Setup

Set your AWS credentials as environment variables before running any script:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_SESSION_TOKEN="your-session-token"  # Only if using temporary credentials
```

## Available Tools

### 1. S3 Folder Copier

Copies an entire folder structure from one location to another within the same S3 bucket.

#### Usage

```bash
python s3_folder_copier.py s3://bucket-name/source-folder/ s3://bucket-name/destination-folder/ [--max-workers N]
```

#### Options

- `source_path`: Source S3 path (e.g., s3://bucket-name/source-prefix/)
- `dest_path`: Destination S3 path (e.g., s3://bucket-name/dest-prefix/)
- `--max-workers`: Maximum number of concurrent copy operations (default: 10)

#### Examples

```bash
# Basic copy operation
python s3_folder_copier.py s3://mybucket/original-data/ s3://mybucket/backup-data/

# Increase concurrent operations for faster copying of many small files
python s3_folder_copier.py s3://mybucket/logs/ s3://mybucket/archived-logs/ --max-workers 20

# Make a version-stamped backup
python s3_folder_copier.py s3://mybucket/website/ s3://mybucket/website-backups/2025-03-22/
```

### 2. S3 Directory Downloader

Downloads a complete directory structure from S3 to your local machine.

#### Usage

```bash
python s3_downloader.py s3://bucket-name/folder/ /path/to/local/directory [--max-workers N]
```

#### Options

- `s3_path`: S3 path (e.g., s3://bucket-name/prefix/)
- `local_directory`: Local directory to save files
- `--max-workers`: Maximum number of concurrent downloads (default: 10)

#### Examples

```bash
# Download S3 folder to local directory
python s3_downloader.py s3://mybucket/photos/ ./downloaded-photos

# Download with more concurrent workers for faster downloading
python s3_downloader.py s3://mybucket/photos/ ./downloaded-photos --max-workers 20
```

## Performance Considerations

- Increase `--max-workers` when dealing with many small files
- Reduce `--max-workers` when dealing with fewer large files
- The default setting of 10 workers is a balanced choice for most operations

## Troubleshooting

If you encounter errors like:

```
botocore.exceptions.ClientError: An error occurred (403) when calling the HeadObject operation: Forbidden
```

Ensure your AWS credentials have the necessary permissions for the S3 bucket operations.

If you see:

```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

Make sure you've properly set your AWS credentials in environment variables or AWS configuration files.