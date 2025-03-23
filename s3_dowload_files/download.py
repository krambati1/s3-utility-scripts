#!/usr/bin/env python3
import os
import sys
import boto3
from botocore.exceptions import ClientError
import argparse
from concurrent.futures import ThreadPoolExecutor
import threading

class S3DirectoryDownloader:
    def __init__(self):
        """
        Initialize S3 Directory Downloader
        
        Uses AWS credentials from environment variables:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_SESSION_TOKEN
        """
        # Create S3 client using credentials from environment variables
        self.s3_client = boto3.client('s3')
        self.s3_resource = boto3.resource('s3')
        
        # Initialize counters
        self.total_files = 0
        self.downloaded_files = 0
        self.download_errors = 0
        self.lock = threading.Lock()
        
    def _parse_s3_path(self, s3_path):
        """
        Parse S3 path into bucket name and prefix
        
        Args:
            s3_path (str): S3 path in format s3://bucket-name/prefix/
        
        Returns:
            tuple: (bucket_name, prefix)
        """
        # Remove s3:// if present
        if s3_path.startswith('s3://'):
            s3_path = s3_path[5:]
        
        # Split into bucket and prefix
        parts = s3_path.split('/', 1)
        bucket_name = parts[0]
        prefix = parts[1] if len(parts) > 1 else ''
        
        # Ensure prefix ends with a / if it's not empty
        if prefix and not prefix.endswith('/'):
            prefix += '/'
        
        return bucket_name, prefix
    
    def download_file(self, bucket_name, key, local_path):
        """
        Download a single file from S3
        
        Args:
            bucket_name (str): S3 bucket name
            key (str): S3 object key
            local_path (str): Local path to save the file
        
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download the file
            self.s3_client.download_file(bucket_name, key, local_path)
            
            with self.lock:
                self.downloaded_files += 1
                
            # Print progress
            print(f"Downloaded: {key} to {local_path}")
            return True
            
        except ClientError as e:
            with self.lock:
                self.download_errors += 1
            
            print(f"Error downloading {key}: {e}")
            return False
    
    def download_directory(self, s3_path, local_directory, max_workers=10):
        """
        Download a complete directory from S3
        
        Args:
            s3_path (str): S3 path in format s3://bucket-name/prefix/
            local_directory (str): Local directory to save files
            max_workers (int, optional): Maximum number of concurrent downloads
        """
        # Parse S3 path
        bucket_name, prefix = self._parse_s3_path(s3_path)
        
        print(f"Downloading from s3://{bucket_name}/{prefix} to {local_directory}")
        
        # Create local directory if it doesn't exist
        os.makedirs(local_directory, exist_ok=True)
        
        # List all objects in the directory
        paginator = self.s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        
        # Set up thread pool for parallel downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            # Process each page of results
            for page in page_iterator:
                if 'Contents' not in page:
                    print(f"No objects found in s3://{bucket_name}/{prefix}")
                    continue
                
                # Process each object
                for obj in page['Contents']:
                    key = obj['Key']
                    self.total_files += 1
                    
                    # Calculate relative path
                    if prefix:
                        relative_path = key[len(prefix):]
                    else:
                        relative_path = key
                    
                    # Skip if it's a directory marker (object ending with /)
                    if relative_path == '' or key.endswith('/'):
                        continue
                    
                    # Construct local file path
                    local_path = os.path.join(local_directory, relative_path)
                    
                    # Submit download task
                    future = executor.submit(self.download_file, bucket_name, key, local_path)
                    futures.append(future)
            
            # Wait for all downloads to complete
            for future in futures:
                future.result()
    
    def print_summary(self):
        """
        Print download summary
        """
        print("\n--- Download Summary ---")
        print(f"Total Files: {self.total_files}")
        print(f"Files Downloaded: {self.downloaded_files}")
        print(f"Download Errors: {self.download_errors}")
        print(f"Success Rate: {(self.downloaded_files / self.total_files * 100):.2f}%" 
              if self.total_files > 0 else "No files processed")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download a complete directory from S3')
    parser.add_argument('s3_path', help='S3 path (e.g., s3://bucket-name/prefix/)')
    parser.add_argument('local_directory', help='Local directory to save files')
    parser.add_argument('--max-workers', type=int, default=10, help='Maximum number of concurrent downloads')
    
    args = parser.parse_args()
    
    # Validate local directory
    if not os.path.isdir(args.local_directory) and os.path.exists(args.local_directory):
        print(f"Error: {args.local_directory} exists but is not a directory")
        sys.exit(1)
    
    # Create downloader and run
    downloader = S3DirectoryDownloader()
    
    try:
        downloader.download_directory(args.s3_path, args.local_directory, args.max_workers)
        downloader.print_summary()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()