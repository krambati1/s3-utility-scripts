# S3 Directory Downloader

A Python utility for downloading complete directory structures from Amazon S3 to your local machine.

## Features

- Downloads entire S3 directories while preserving folder structure
- Multi-threaded downloading for improved performance
- Progress tracking for large downloads
- Detailed summary report
- Automatic creation of local directories as needed

## Requirements

- Python 3.6+
- boto3 library

Install required dependencies:
```bash
pip install boto3
```

## AWS Authentication

This script uses the standard AWS credential chain. Before running, make sure your AWS credentials are properly configured using one of these methods:

1. **Environment variables**:
   ```bash
   export AWS_ACCESS_KEY_ID="your-access-key"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"
   export AWS_SESSION_TOKEN="your-session-token"  # Only if using temporary credentials
   ```

2. **AWS credentials file**:
   ```
   # ~/.aws/credentials
   [default]
   aws_access_key_id = your-access-key
   aws_secret_access_key = your-secret-key
   ```

3. **IAM Role**: If running on an EC2 instance with an assigned IAM role

## Usage

```bash
python download.py s3://bucket-name/folder/ /path/to/local/directory [--max-workers N]
```

### Parameters

- `s3_path`: Source S3 path (required)
- `local_directory`: Local directory where files will be saved (required)
- `--max-workers`: Number of concurrent download threads (optional, default: 10)

### Examples

1. **Basic download**:
   ```bash
   python download.py s3://my-bucket/data/ ./downloaded-data
   ```

2. **Increase download speed** with more worker threads:
   ```bash
   python download.py s3://my-bucket/photos/ ./my-photos --max-workers 20
   ```

3. **Download to a specific path**:
   ```bash
   python download.py s3://my-bucket/logs/2023/ /var/backups/logs
   ```

## Performance Tuning

- For many small files, increase the `--max-workers` value (e.g., 20-30)
- For fewer large files, a lower number of workers might be more efficient (e.g., 5-10)
- The default setting of 10 workers is generally a good starting point

## Error Handling

The script handles common errors such as:
- Non-existent S3 paths
- Permission issues
- Network interruptions

Failed downloads are logged and counted in the summary report.

## Output

The script provides real-time progress information and a summary after completion:

```
Downloading from s3://my-bucket/photos/ to ./downloaded-photos
Downloaded: photos/vacation/img001.jpg to ./downloaded-photos/vacation/img001.jpg
Downloaded: photos/vacation/img002.jpg to ./downloaded-photos/vacation/img002.jpg
...

--- Download Summary ---
Total Files: 125
Files Downloaded: 123
Download Errors: 2
Success Rate: 98.40%
```

## Troubleshooting

- **Access Denied errors**: Verify your AWS credentials have sufficient permissions
- **No objects found**: Check if the S3 path is correct and contains files
- **Connection errors**: Check your network connection and try again

