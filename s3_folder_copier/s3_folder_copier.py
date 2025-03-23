#!/usr/bin/env python3
import os
import sys
import boto3
from botocore.exceptions import ClientError
import argparse
from concurrent.futures import ThreadPoolExecutor
import threading
import time

class S3FolderCopier:
    def __init__(self):
        """
        Initialize S3 Folder Copier
        
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
        self.copied_files = 0
        self.copy_errors = 0
        self.start_time = 0
        self.end_time = 0
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
    
    def copy_object(self, bucket_name, source_key, dest_key):
        """
        Copy a single object within the same bucket
        
        Args:
            bucket_name (str): S3 bucket name
            source_key (str): Source object key
            dest_key (str): Destination object key
        
        Returns:
            bool: True if copy was successful, False otherwise
        """
        try:
            # Create copy source dictionary
            copy_source = {
                'Bucket': bucket_name,
                'Key': source_key
            }
            
            # Copy the object
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=bucket_name,
                Key=dest_key
            )
            
            with self.lock:
                self.copied_files += 1
                
            # Print progress with percentage
            percentage = (self.copied_files / self.total_files) * 100 if self.total_files > 0 else 0
            print(f"Copied: {source_key} to {dest_key} - Progress: {percentage:.1f}%")
            return True
            
        except ClientError as e:
            with self.lock:
                self.copy_errors += 1
            
            print(f"Error copying {source_key}: {e}")
            return False
    
    def copy_folder(self, source_s3_path, dest_s3_path, max_workers=10):
        """
        Copy a complete folder within the same S3 bucket
        
        Args:
            source_s3_path (str): Source S3 path in format s3://bucket-name/prefix/
            dest_s3_path (str): Destination S3 path in format s3://bucket-name/prefix/
            max_workers (int, optional): Maximum number of concurrent copy operations
        """
        # Parse S3 paths
        source_bucket, source_prefix = self._parse_s3_path(source_s3_path)
        dest_bucket, dest_prefix = self._parse_s3_path(dest_s3_path)
        
        # Ensure we're operating within the same bucket
        if source_bucket != dest_bucket:
            raise ValueError("Source and destination buckets must be the same for this script")
            
        print(f"Copying from s3://{source_bucket}/{source_prefix} to s3://{dest_bucket}/{dest_prefix}")
        
        # List all objects in the source directory
        paginator = self.s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=source_bucket, Prefix=source_prefix)
        
        # First, count total files to copy
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Skip if it's a directory marker (object ending with /)
                    if key.endswith('/'):
                        continue
                        
                    self.total_files += 1
        
        # If there are no files to copy, exit early
        if self.total_files == 0:
            print(f"No objects found in s3://{source_bucket}/{source_prefix}")
            return
            
        # Reset paginator for actual copying
        page_iterator = paginator.paginate(Bucket=source_bucket, Prefix=source_prefix)
        
        # Set up thread pool for parallel copies
        self.start_time = time.time()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            # Process each page of results
            for page in page_iterator:
                if 'Contents' not in page:
                    continue
                
                # Process each object
                for obj in page['Contents']:
                    source_key = obj['Key']
                    
                    # Skip if it's a directory marker (object ending with /)
                    if source_key.endswith('/'):
                        continue
                    
                    # Calculate relative path and construct destination key
                    if source_prefix:
                        relative_path = source_key[len(source_prefix):]
                    else:
                        relative_path = source_key
                    
                    dest_key = dest_prefix + relative_path
                    
                    # Submit copy task
                    future = executor.submit(self.copy_object, source_bucket, source_key, dest_key)
                    futures.append(future)
            
            # Wait for all copies to complete
            for future in futures:
                future.result()
                
        self.end_time = time.time()
    
    def print_summary(self):
        """
        Print copy operation summary
        """
        elapsed_time = self.end_time - self.start_time
        bytes_per_second = 0
        
        print("\n--- Copy Summary ---")
        print(f"Total Files: {self.total_files}")
        print(f"Files Copied: {self.copied_files}")
        print(f"Copy Errors: {self.copy_errors}")
        print(f"Success Rate: {(self.copied_files / self.total_files * 100):.2f}%" 
              if self.total_files > 0 else "No files processed")
        print(f"Elapsed Time: {elapsed_time:.2f} seconds")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Copy a complete folder within the same S3 bucket')
    parser.add_argument('source_path', help='Source S3 path (e.g., s3://bucket-name/source-prefix/)')
    parser.add_argument('dest_path', help='Destination S3 path (e.g., s3://bucket-name/dest-prefix/)')
    parser.add_argument('--max-workers', type=int, default=10, help='Maximum number of concurrent copy operations')
    
    args = parser.parse_args()
    
    # Create copier and run
    copier = S3FolderCopier()
    
    try:
        copier.copy_folder(args.source_path, args.dest_path, args.max_workers)
        copier.print_summary()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()