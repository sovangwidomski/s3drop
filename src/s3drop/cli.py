#!/usr/bin/env python3
"""
S3-Drop v1.0.0
Professional S3 presigned URL generator with drag & drop HTML interfaces
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

VERSION = "1.0.0"

class S3DropConfig:
    """Manage S3-Drop configuration and state."""
    
    def __init__(self):
        self.config_dir = Path.home() / '.s3drop'
        self.config_file = self.config_dir / 'config.json'
        self.history_file = self.config_dir / 'history.json'
        self.config_dir.mkdir(exist_ok=True)
        
        self.config = self._load_config()
        self.history = self._load_history()
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        default_config = {
            'default_bucket': '',
            'default_region': 'us-east-1',
            'default_prefix': 'uploads',
            'default_max_size_mb': 5120,  # 5GB
            'default_expiration_hours': 1,
            'verify_ssl': True,
            'favorite_buckets': [],
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for any missing keys
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception:
                pass
        
        return default_config
    
    def _load_history(self) -> List[Dict]:
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                    # Keep only last 50 entries
                    return history[-50:]
            except Exception:
                pass
        return []
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Could not save config: {e}")
    
    def save_history(self):
        """Save history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history[-50:], f, indent=2)  # Keep last 50
        except Exception as e:
            print(f"⚠️  Warning: Could not save history: {e}")
    
    def add_to_history(self, operation: str, bucket: str, details: Dict):
        """Add operation to history."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'bucket': bucket,
            **details
        }
        self.history.append(entry)
        self.save_history()
    
    def add_favorite_bucket(self, bucket: str):
        """Add bucket to favorites."""
        if bucket not in self.config['favorite_buckets']:
            self.config['favorite_buckets'].append(bucket)
            self.save_config()
    
    def remove_favorite_bucket(self, bucket: str):
        """Remove bucket from favorites."""
        if bucket in self.config['favorite_buckets']:
            self.config['favorite_buckets'].remove(bucket)
            self.save_config()


class S3DropClient:
    """S3 client wrapper with enhanced functionality."""
    
    def __init__(self, region: str = 'us-east-1', verify_ssl: bool = True):
        self.region = region
        self.verify_ssl = verify_ssl
        self._client = None
    
    @property
    def client(self):
        """Lazy load S3 client."""
        if self._client is None:
            try:
                session = boto3.Session()
                self._client = session.client(
                    's3',
                    region_name=self.region,
                    verify=self.verify_ssl
                )
            except Exception as e:
                raise ClientError(
                    error_response={'Error': {'Code': 'ConfigError', 'Message': str(e)}},
                    operation_name='CreateClient'
                )
        return self._client
    
    def list_buckets(self) -> List[str]:
        """List all accessible S3 buckets."""
        try:
            response = self.client.list_buckets()
            return [bucket['Name'] for bucket in response['Buckets']]
        except Exception:
            return []
    
    def bucket_exists(self, bucket: str) -> bool:
        """Check if bucket exists and is accessible."""
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except Exception:
            return False
    
    def get_bucket_region(self, bucket: str) -> Optional[str]:
        """Get bucket region."""
        try:
            response = self.client.get_bucket_location(Bucket=bucket)
            region = response['LocationConstraint']
            return region or 'us-east-1'  # us-east-1 returns None
        except Exception:
            return None
    
    def check_cors(self, bucket: str) -> bool:
        """Check if bucket has CORS configured."""
        try:
            self.client.get_bucket_cors(Bucket=bucket)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
                return False
            raise
    
    def setup_cors(self, bucket: str) -> bool:
        """Set up CORS configuration for bucket."""
        cors_config = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'POST', 'PUT'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': [],
                    'MaxAgeSeconds': 3600
                }
            ]
        }
        
        try:
            self.client.put_bucket_cors(
                Bucket=bucket,
                CORSConfiguration=cors_config
            )
            return True
        except Exception:
            return False
    
    def generate_presigned_post(self, bucket: str, prefix: str = '', 
                              max_size_bytes: int = 5368709120, 
                              allowed_types: Optional[List[str]] = None,
                              expiration_seconds: int = 3600) -> Dict:
        """Generate presigned POST for file uploads."""
        key = f"{prefix}/${{filename}}" if prefix else "${filename}"
        
        conditions = [
            ['content-length-range', 0, max_size_bytes]
        ]
        
        if allowed_types:
            for file_type in allowed_types:
                conditions.append(['starts-with', '$Content-Type', file_type])
        
        try:
            response = self.client.generate_presigned_post(
                Bucket=bucket,
                Key=key,
                Conditions=conditions,
                ExpiresIn=expiration_seconds
            )
            return response
        except Exception as e:
            raise ClientError(
                error_response={'Error': {'Code': 'PresignedPostError', 'Message': str(e)}},
                operation_name='GeneratePresignedPost'
            )
    
    def list_objects(self, bucket: str, prefix: str = '', max_keys: int = 100) -> List[Dict]:
        """List objects in S3 bucket."""
        try:
            params = {
                'Bucket': bucket,
                'MaxKeys': max_keys
            }
            if prefix:
                params['Prefix'] = prefix
                
            response = self.client.list_objects_v2(**params)
            
            objects = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    objects.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'modified': obj['LastModified'],
                        'storage_class': obj.get('StorageClass', 'STANDARD')
                    })
            
            return sorted(objects, key=lambda x: x['key'])
        except Exception:
            return []
    
    def list_prefixes(self, bucket: str, prefix: str = '', delimiter: str = '/') -> List[str]:
        """List common prefixes (folders) in S3 bucket."""
        try:
            params = {
                'Bucket': bucket,
                'Delimiter': delimiter,
                'MaxKeys': 100
            }
            if prefix:
                params['Prefix'] = prefix
                
            response = self.client.list_objects_v2(**params)
            
            prefixes = []
            if 'CommonPrefixes' in response:
                for cp in response['CommonPrefixes']:
                    prefixes.append(cp['Prefix'])
            
            return sorted(prefixes)
        except Exception:
            return []
    
    def generate_presigned_url(self, bucket: str, key: str, 
                             expiration_seconds: int = 3600, 
                             method: str = 'get_object') -> str:
        """Generate presigned URL for file download/upload."""
        try:
            url = self.client.generate_presigned_url(
                method,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration_seconds
            )
            return url
        except Exception as e:
            raise ClientError(
                error_response={'Error': {'Code': 'PresignedUrlError', 'Message': str(e)}},
                operation_name='GeneratePresignedUrl'
            )


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def generate_download_instructions(download_url: str, bucket: str, key: str, expiration_time: datetime) -> str:
    """Generate HTML file with download instructions."""
    expiration_display = expiration_time.strftime('%B %d, %Y at %I:%M %p')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S3-Drop Download Link</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .download-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2em;
        }}
        
        .header .subtitle {{
            color: #7f8c8d;
            font-size: 1.1em;
        }}
        
        .file-info {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .file-info h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
        }}
        
        .file-detail {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .file-detail:last-child {{
            border-bottom: none;
            margin-bottom: 0;
        }}
        
        .download-section {{
            background: #e8f5e8;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }}
        
        .download-url {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            font-family: monospace;
            font-size: 14px;
            word-break: break-all;
            margin: 15px 0;
            color: #495057;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-block;
            text-decoration: none;
            margin: 5px;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .btn-success {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }}
        
        .btn-secondary {{
            background: #6c757d;
        }}
        
        .instructions {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .instructions h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
        }}
        
        .instructions ol {{
            color: #495057;
            padding-left: 20px;
        }}
        
        .instructions li {{
            margin-bottom: 8px;
            line-height: 1.5;
        }}
        
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .warning strong {{
            color: #856404;
        }}
        
        @media (max-width: 600px) {{
            .download-container {{
                padding: 30px 20px;
            }}
            
            .header h1 {{
                font-size: 1.5em;
            }}
            
            .file-detail {{
                flex-direction: column;
                gap: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="download-container">
        <div class="header">
            <h1>📥 S3-Drop Download</h1>
            <div class="subtitle">Secure file download link</div>
        </div>
        
        <div class="file-info">
            <h3>📋 File Information</h3>
            <div class="file-detail">
                <span><strong>Bucket:</strong></span>
                <span>{bucket}</span>
            </div>
            <div class="file-detail">
                <span><strong>File Path:</strong></span>
                <span>{key}</span>
            </div>
            <div class="file-detail">
                <span><strong>Expires:</strong></span>
                <span>{expiration_display}</span>
            </div>
        </div>
        
        <div class="download-section">
            <h3>🔗 Download Link</h3>
            <div class="download-url" id="downloadUrl">{download_url}</div>
            <button class="btn btn-success" onclick="downloadFile()">📥 Download File</button>
            <button class="btn btn-secondary" onclick="copyUrl()">📋 Copy Link</button>
        </div>
        
        <div class="instructions">
            <h3>📖 How to Use This Link</h3>
            <ol>
                <li><strong>Click "Download File"</strong> to download immediately</li>
                <li><strong>Copy the link</strong> to share with others</li>
                <li><strong>Right-click "Download File"</strong> and "Save Link As..." to save to a specific location</li>
                <li><strong>The link works in any browser</strong> - no AWS account needed</li>
                <li><strong>Share safely</strong> - anyone with this link can download the file</li>
            </ol>
        </div>
        
        <div class="warning">
            <strong>⚠️ Important:</strong> This download link expires on {expiration_display}. After that time, the link will no longer work and you'll need to generate a new one.
        </div>
    </div>

    <script>
        function downloadFile() {{
            window.open('{download_url}', '_blank');
        }}

        function copyUrl() {{
            const url = document.getElementById('downloadUrl').textContent;
            navigator.clipboard.writeText(url).then(() => {{
                // Temporarily change button text
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '✅ Copied!';
                setTimeout(() => {{
                    btn.textContent = originalText;
                }}, 2000);
            }}).catch(() => {{
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = url;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '✅ Copied!';
                setTimeout(() => {{
                    btn.textContent = originalText;
                }}, 2000);
            }});
        }}
    </script>
</body>
</html>"""


def format_duration(seconds: int) -> str:
    """Format duration in human readable format."""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        return f"{seconds // 60} minutes"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes == 0:
            return f"{hours} hours"
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        if hours == 0:
            return f"{days} days"
        return f"{days}d {hours}h"


def generate_upload_html(presigned_post: Dict, config_data: Dict) -> str:
    """Generate HTML upload form with improved success handling."""
    url = presigned_post['url']
    fields = presigned_post['fields']
    
    max_size_mb = config_data.get('max_size_mb', 5120)
    max_size_bytes = max_size_mb * 1024 * 1024
    bucket = config_data.get('bucket', 'unknown')
    prefix = config_data.get('prefix', '')
    allowed_types = config_data.get('allowed_types', [])
    expiration_hours = config_data.get('expiration_hours', 1)
    
    # Calculate actual expiration time
    expiration_time = datetime.now() + timedelta(hours=expiration_hours)
    expiration_display = expiration_time.strftime('%B %d, %Y at %I:%M %p')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S3-Drop File Upload</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .upload-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2em;
        }}
        
        .header .subtitle {{
            color: #7f8c8d;
            font-size: 1.1em;
        }}
        
        .upload-area {{
            border: 3px dashed #bdc3c7;
            border-radius: 12px;
            padding: 60px 40px;
            text-align: center;
            margin: 30px 0;
            transition: all 0.3s ease;
            cursor: pointer;
            background: #f8f9fa;
        }}
        
        .upload-area:hover {{
            border-color: #667eea;
            background: #f0f3ff;
            transform: translateY(-2px);
        }}
        
        .upload-area.dragover {{
            border-color: #667eea;
            background: #e8f0fe;
            transform: scale(1.02);
        }}
        
        .upload-area.hidden {{
            display: none;
        }}
        
        .upload-icon {{
            font-size: 4em;
            margin-bottom: 20px;
            color: #bdc3c7;
        }}
        
        .upload-area.dragover .upload-icon {{
            color: #667eea;
        }}
        
        .upload-text {{
            font-size: 1.2em;
            color: #2c3e50;
            margin-bottom: 15px;
        }}
        
        .upload-subtext {{
            color: #7f8c8d;
            margin-bottom: 20px;
        }}
        
        #fileInput {{
            display: none;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-block;
            text-decoration: none;
            margin: 5px;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .btn:disabled {{
            background: #95a5a6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }}
        
        .btn-secondary {{
            background: #6c757d;
        }}
        
        .btn-secondary:hover {{
            background: #545b62;
        }}
        
        .file-info {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            display: none;
        }}
        
        .file-info h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
        }}
        
        .file-detail {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .file-detail:last-child {{
            border-bottom: none;
            margin-bottom: 0;
        }}
        
        .progress-container {{
            margin: 20px 0;
            display: none;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            position: relative;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s ease;
            position: relative;
        }}
        
        .progress-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #2c3e50;
            font-weight: 600;
            font-size: 12px;
        }}
        
        .status {{
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            display: none;
            font-weight: 500;
        }}
        
        .status.success {{
            background-color: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }}
        
        .status.error {{
            background-color: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }}
        
        /* New styles for upload history */
        .upload-history {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            display: none;
        }}
        
        .upload-history h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .upload-item {{
            background: white;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #28a745;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .upload-item:last-child {{
            margin-bottom: 0;
        }}
        
        .upload-item-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        
        .upload-item-name {{
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .upload-item-time {{
            font-size: 0.9em;
            color: #6c757d;
        }}
        
        .upload-item-details {{
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        
        .success-actions {{
            margin-top: 15px;
        }}
        
        .limits {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 30px;
        }}
        
        .limits h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.1em;
        }}
        
        .limits ul {{
            list-style: none;
            color: #7f8c8d;
        }}
        
        .limits li {{
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }}
        
        .limits li::before {{
            content: "✓";
            color: #28a745;
            font-weight: bold;
            margin-right: 10px;
        }}
        
        /* Celebration animation */
        @keyframes celebrate {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); }}
        }}
        
        .celebrate {{
            animation: celebrate 0.6s ease-in-out;
        }}
        
        @media (max-width: 600px) {{
            .upload-container {{
                padding: 30px 20px;
            }}
            
            .upload-area {{
                padding: 40px 20px;
            }}
            
            .header h1 {{
                font-size: 1.5em;
            }}
            
            .upload-item-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="upload-container">
        <div class="header">
            <h1>📤 S3-Drop</h1>
            <div class="subtitle">Secure file upload to {bucket}</div>
        </div>
        
        <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
            <div class="upload-icon">📁</div>
            <div class="upload-text">Drop your file here</div>
            <div class="upload-subtext">or click to browse</div>
            <button class="btn" type="button">Choose File</button>
            <input type="file" id="fileInput" accept="*/*" {('accept="' + ','.join(allowed_types) + '"') if allowed_types else ''}>
        </div>
        
        <div class="file-info" id="fileInfo">
            <h3>📋 File Details</h3>
            <div class="file-detail">
                <span><strong>File:</strong></span>
                <span id="fileName"></span>
            </div>
            <div class="file-detail">
                <span><strong>Size:</strong></span>
                <span id="fileSize"></span>
            </div>
            <div class="file-detail">
                <span><strong>Upload to:</strong></span>
                <span id="finalPath"></span>
            </div>
            <button class="btn" id="uploadBtn" onclick="uploadFile()" style="margin-top: 15px;">
                🚀 Upload File
            </button>
        </div>
        
        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
                <div class="progress-text" id="progressText">0%</div>
            </div>
        </div>
        
        <div class="status" id="status"></div>
        
        <!-- New upload history section -->
        <div class="upload-history" id="uploadHistory">
            <h3>✅ Completed Uploads <span id="uploadCount">(0)</span></h3>
            <div id="uploadList"></div>
            <div class="success-actions">
                <button class="btn" onclick="startNewUpload()">📁 Upload Another File</button>
                <button class="btn btn-secondary" onclick="copyLastUrl()" id="copyUrlBtn" style="display: none;">📋 Copy Last S3 URL</button>
            </div>
        </div>
        
        <div class="limits">
            <h3>📝 Upload Limits</h3>
            <ul>
                <li>Maximum file size: {format_file_size(max_size_bytes)}</li>
                <li>Upload expires: {expiration_display}</li>
                {('<li>Allowed types: ' + ', '.join(allowed_types) + '</li>') if allowed_types else '<li>All file types allowed</li>'}
                <li>Files upload directly to S3 (secure)</li>
            </ul>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const finalPath = document.getElementById('finalPath');
        const uploadBtn = document.getElementById('uploadBtn');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const status = document.getElementById('status');
        const uploadHistory = document.getElementById('uploadHistory');
        const uploadList = document.getElementById('uploadList');
        const uploadCount = document.getElementById('uploadCount');
        const copyUrlBtn = document.getElementById('copyUrlBtn');
        
        let selectedFile = null;
        let uploadCounter = 0;
        let completedUploads = [];
        const uploadUrl = '{url}';
        const prefix = '{prefix}';
        const maxFileSize = {max_size_bytes};
        const bucket = '{bucket}';
        const expiresAt = '{expiration_display}';

        // Sound for success (optional - works in most browsers)
        function playSuccessSound() {{
            try {{
                const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsiCT2YzO/OgiMGMnvC7+GVSA0PVajh8bllHgg2jdXz0H0vBSF+zPLaizsIGGS5+OOeLQ==');
                audio.volume = 0.3;
                audio.play().catch(() => {{}}); // Ignore if audio fails
            }} catch (e) {{
                // Ignore audio errors
            }}
        }}

        // Drag and drop handlers
        uploadArea.addEventListener('dragover', (e) => {{
            e.preventDefault();
            uploadArea.classList.add('dragover');
        }});

        uploadArea.addEventListener('dragleave', () => {{
            uploadArea.classList.remove('dragover');
        }});

        uploadArea.addEventListener('drop', (e) => {{
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {{
                handleFileSelect(files[0]);
            }}
        }});

        fileInput.addEventListener('change', (e) => {{
            if (e.target.files.length > 0) {{
                handleFileSelect(e.target.files[0]);
            }}
        }});

        function formatFileSize(bytes) {{
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }}

        function formatTime(date) {{
            return date.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}});
        }}

        function handleFileSelect(file) {{
            if (file.size > maxFileSize) {{
                showStatus('File too large. Maximum size is ' + formatFileSize(maxFileSize), 'error');
                return;
            }}

            selectedFile = file;
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            
            const finalKey = prefix ? prefix + '/' + file.name : file.name;
            finalPath.textContent = finalKey;
            
            fileInfo.style.display = 'block';
            hideStatus();
        }}

        async function uploadFile() {{
            if (!selectedFile) return;

            uploadBtn.disabled = true;
            progressContainer.style.display = 'block';
            hideStatus();

            const formData = new FormData();
            
            // Add presigned POST fields (safely encoded)
            const presignedFields = {json.dumps(fields)};
            Object.entries(presignedFields).forEach(([key, value]) => {{
                formData.append(key, value);
            }});
            
            // Replace ${{filename}} with actual filename
            const actualKey = formData.get('key').replace('${{filename}}', selectedFile.name);
            formData.set('key', actualKey);
            
            // Add file
            formData.append('file', selectedFile);

            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {{
                if (e.lengthComputable) {{
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    progressFill.style.width = percentComplete + '%';
                    progressText.textContent = percentComplete + '%';
                }}
            }});

            xhr.onload = function() {{
                if (xhr.status === 204 || xhr.status === 200) {{
                    // Success! Add to history and show persistent confirmation
                    const uploadInfo = {{
                        name: selectedFile.name,
                        size: selectedFile.size,
                        key: actualKey,
                        time: new Date(),
                        s3Url: `https://${{bucket}}.s3.amazonaws.com/${{actualKey}}`
                    }};
                    
                    addToUploadHistory(uploadInfo);
                    showPersistentSuccess(uploadInfo);
                    
                    // Play success sound
                    playSuccessSound();
                    
                    // Celebration animation
                    document.querySelector('.upload-container').classList.add('celebrate');
                    setTimeout(() => {{
                        document.querySelector('.upload-container').classList.remove('celebrate');
                    }}, 600);
                    
                    progressFill.style.width = '100%';
                    progressText.textContent = '100%';
                    
                    // Hide upload area and file info, show history
                    uploadArea.classList.add('hidden');
                    fileInfo.style.display = 'none';
                    uploadHistory.style.display = 'block';
                    
                }} else {{
                    showStatus('Upload failed (Status ' + xhr.status + '): ' + (xhr.responseText || xhr.statusText), 'error');
                    uploadBtn.disabled = false;
                }}
            }};

            xhr.onerror = function() {{
                showStatus('Upload failed: Network error. Check your connection and try again.', 'error');
                uploadBtn.disabled = false;
            }};

            xhr.open('POST', uploadUrl);
            xhr.send(formData);
        }}

        function addToUploadHistory(uploadInfo) {{
            completedUploads.push(uploadInfo);
            uploadCounter++;
            
            // Update counter
            uploadCount.textContent = `(${{uploadCounter}})`;
            
            // Create upload item
            const uploadItem = document.createElement('div');
            uploadItem.className = 'upload-item';
            uploadItem.innerHTML = `
                <div class="upload-item-header">
                    <div class="upload-item-name">📁 ${{uploadInfo.name}}</div>
                    <div class="upload-item-time">${{formatTime(uploadInfo.time)}}</div>
                </div>
                <div class="upload-item-details">
                    <strong>Size:</strong> ${{formatFileSize(uploadInfo.size)}} • 
                    <strong>Location:</strong> ${{uploadInfo.key}}
                </div>
            `;
            
            // Add to top of list
            uploadList.insertBefore(uploadItem, uploadList.firstChild);
            
            // Show copy URL button
            copyUrlBtn.style.display = 'inline-block';
        }}

        function showPersistentSuccess(uploadInfo) {{
            const message = `🎉 Successfully uploaded "${{uploadInfo.name}}" to S3!<br>
                           <small>Location: ${{uploadInfo.key}}</small>`;
            status.innerHTML = message;
            status.className = 'status success';
            status.style.display = 'block';
            
            // Don't hide the status - let it stay visible
        }}

        function startNewUpload() {{
            // Reset for new upload
            selectedFile = null;
            fileInput.value = '';
            uploadArea.classList.remove('hidden');
            fileInfo.style.display = 'none';
            progressContainer.style.display = 'none';
            progressFill.style.width = '0%';
            progressText.textContent = '0%';
            uploadBtn.disabled = false;
            hideStatus();
        }}

        function copyLastUrl() {{
            if (completedUploads.length > 0) {{
                const lastUpload = completedUploads[completedUploads.length - 1];
                navigator.clipboard.writeText(lastUpload.s3Url).then(() => {{
                    // Temporarily change button text
                    const originalText = copyUrlBtn.textContent;
                    copyUrlBtn.textContent = '✅ Copied!';
                    setTimeout(() => {{
                        copyUrlBtn.textContent = originalText;
                    }}, 2000);
                }}).catch(() => {{
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = lastUpload.s3Url;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    
                    const originalText = copyUrlBtn.textContent;
                    copyUrlBtn.textContent = '✅ Copied!';
                    setTimeout(() => {{
                        copyUrlBtn.textContent = originalText;
                    }}, 2000);
                }});
            }}
        }}

        function showStatus(message, type) {{
            status.innerHTML = message;
            status.className = 'status ' + type;
            status.style.display = 'block';
        }}

        function hideStatus() {{
            status.style.display = 'none';
        }}
    </script>
</body>
</html>"""


def list_buckets(config: S3DropConfig) -> List[str]:
    """List available S3 buckets."""
    client = S3DropClient(config.config['default_region'], config.config['verify_ssl'])
    try:
        buckets = client.list_buckets()
        return sorted(buckets)
    except Exception:
        return []


def show_current_config(config: S3DropConfig):
    """Display current configuration."""
    print(f"\n🔧 S3-Drop Configuration")
    print("=" * 50)
    print(f"📍 Default bucket: {config.config['default_bucket'] or 'Not set'}")
    print(f"🌍 Default region: {config.config['default_region']}")
    print(f"📁 Default prefix: {config.config['default_prefix']}")
    print(f"📏 Default max size: {format_file_size(config.config['default_max_size_mb'] * 1024 * 1024)}")
    print(f"⏰ Default expiration: {format_duration(config.config['default_expiration_hours'] * 3600)}")
    print(f"🔒 SSL verification: {'Enabled' if config.config['verify_ssl'] else 'Disabled'}")
    
    if config.config['favorite_buckets']:
        print(f"\n⭐ Favorite buckets ({len(config.config['favorite_buckets'])}):")
        for i, bucket in enumerate(config.config['favorite_buckets'], 1):
            print(f"   {i}. {bucket}")
    else:
        print(f"\n⭐ No favorite buckets saved")


def show_recent_history(config: S3DropConfig):
    """Display recent operations."""
    if not config.history:
        print("📋 No recent operations")
        return
    
    print(f"\n📋 Recent Operations ({len(config.history)} total)")
    print("=" * 50)
    
    # Show last 10 operations
    recent = config.history[-10:]
    for entry in reversed(recent):
        timestamp = datetime.fromisoformat(entry['timestamp'])
        time_str = timestamp.strftime('%m/%d %H:%M')
        
        operation = entry['operation']
        bucket = entry['bucket']
        
        if operation == 'upload-form':
            prefix = entry.get('prefix', '')
            size = entry.get('max_size_mb', 'unknown')
            print(f"📤 {time_str} - Upload form: {bucket}/{prefix} ({size}MB max)")
        elif operation == 'download':
            key = entry.get('key', '')
            print(f"📥 {time_str} - Download: {bucket}/{key}")
        else:
            print(f"🔧 {time_str} - {operation}: {bucket}")


def configure_settings(config: S3DropConfig):
    """Interactive configuration management."""
    while True:
        print(f"\n🔧 Configuration Settings")
        print("=" * 50)
        print(f"1. Default bucket: {config.config['default_bucket'] or 'Not set'}")
        print(f"2. Default region: {config.config['default_region']}")
        print(f"3. Default prefix: {config.config['default_prefix']}")
        print(f"4. Default max size: {format_file_size(config.config['default_max_size_mb'] * 1024 * 1024)}")
        print(f"5. Default expiration: {format_duration(config.config['default_expiration_hours'] * 3600)}")
        print(f"6. SSL verification: {'Enabled' if config.config['verify_ssl'] else 'Disabled'}")
        print(f"7. Manage favorite buckets")
        print(f"s. Save and return")
        print(f"q. Return without saving")
        
        try:
            choice = input("\nSelect option: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == 's':
                config.save_config()
                print("✅ Configuration saved!")
                break
            elif choice == '1':
                buckets = list_buckets(config)
                if buckets:
                    print(f"\nAvailable buckets:")
                    for i, bucket in enumerate(buckets, 1):
                        print(f"   {i}. {bucket}")
                    
                    bucket_choice = input(f"\nEnter bucket name or number (current: {config.config['default_bucket']}): ").strip()
                    if bucket_choice:
                        try:
                            bucket_num = int(bucket_choice)
                            if 1 <= bucket_num <= len(buckets):
                                config.config['default_bucket'] = buckets[bucket_num - 1]
                        except ValueError:
                            config.config['default_bucket'] = bucket_choice
                else:
                    bucket = input(f"Enter bucket name (current: {config.config['default_bucket']}): ").strip()
                    if bucket:
                        config.config['default_bucket'] = bucket
            elif choice == '2':
                region = input(f"Enter region (current: {config.config['default_region']}): ").strip()
                if region:
                    config.config['default_region'] = region
            elif choice == '3':
                prefix = input(f"Enter prefix (current: {config.config['default_prefix']}): ").strip()
                config.config['default_prefix'] = prefix  # Allow empty
            elif choice == '4':
                try:
                    size_mb = int(input(f"Enter max size in MB (current: {config.config['default_max_size_mb']}): ").strip())
                    if size_mb > 0:
                        config.config['default_max_size_mb'] = size_mb
                except ValueError:
                    print("❌ Please enter a valid number")
            elif choice == '5':
                try:
                    hours = float(input(f"Enter expiration in hours (current: {config.config['default_expiration_hours']}): ").strip())
                    if hours > 0:
                        config.config['default_expiration_hours'] = hours
                except ValueError:
                    print("❌ Please enter a valid number")
            elif choice == '6':
                ssl_choice = input("Enable SSL verification? (y/n): ").strip().lower()
                config.config['verify_ssl'] = ssl_choice.startswith('y')
            elif choice == '7':
                manage_favorite_buckets(config)
            else:
                print("❌ Invalid option")
                
        except KeyboardInterrupt:
            print("\n👋 Configuration cancelled")
            break


def manage_favorite_buckets(config: S3DropConfig):
    """Manage favorite buckets."""
    while True:
        print(f"\n⭐ Favorite Buckets")
        print("=" * 30)
        
        if config.config['favorite_buckets']:
            for i, bucket in enumerate(config.config['favorite_buckets'], 1):
                print(f"   {i}. {bucket}")
        else:
            print("   No favorites saved")
        
        print(f"\nOptions:")
        print(f"   a. Add bucket")
        print(f"   r. Remove bucket")
        print(f"   c. Clear all")
        print(f"   b. Back")
        
        try:
            choice = input("\nSelect option: ").strip().lower()
            
            if choice == 'b':
                break
            elif choice == 'a':
                bucket = input("Enter bucket name to add: ").strip()
                if bucket:
                    config.add_favorite_bucket(bucket)
                    print(f"✅ Added {bucket} to favorites")
            elif choice == 'r':
                if not config.config['favorite_buckets']:
                    print("❌ No favorites to remove")
                    continue
                    
                try:
                    choice_num = int(input("Enter number to remove: ").strip())
                    if 1 <= choice_num <= len(config.config['favorite_buckets']):
                        bucket = config.config['favorite_buckets'][choice_num - 1]
                        config.remove_favorite_bucket(bucket)
                        print(f"✅ Removed {bucket} from favorites")
                except ValueError:
                    print("❌ Please enter a valid number")
            elif choice == 'c':
                if config.config['favorite_buckets']:
                    confirm = input("Clear all favorites? (y/N): ").strip().lower()
                    if confirm == 'y':
                        config.config['favorite_buckets'] = []
                        print("✅ All favorites cleared")
            else:
                print("❌ Invalid option")
                
        except KeyboardInterrupt:
            print("\n👋 Returning to configuration")
            break


def interactive_upload_form(config: S3DropConfig):
    """Interactive upload form generation."""
    print(f"\n📤 Generate Upload Form")
    print("=" * 50)
    
    # Bucket selection
    bucket = config.config['default_bucket']
    if not bucket or input(f"Use default bucket '{bucket}'? (Y/n): ").strip().lower() == 'n':
        # Show available buckets
        buckets = list_buckets(config)
        favorites = config.config['favorite_buckets']
        
        all_buckets = []
        if favorites:
            print(f"\n⭐ Favorite buckets:")
            for i, fav_bucket in enumerate(favorites, 1):
                print(f"   {i}. {fav_bucket}")
                all_buckets.append(fav_bucket)
        
        if buckets:
            start_num = len(favorites) + 1
            print(f"\n📋 Available buckets:")
            for i, available_bucket in enumerate(buckets, start_num):
                if available_bucket not in favorites:
                    print(f"   {i}. {available_bucket}")
                    all_buckets.append(available_bucket)
        
        if all_buckets:
            try:
                choice = input(f"\nSelect bucket (number or name): ").strip()
                try:
                    bucket_num = int(choice)
                    if 1 <= bucket_num <= len(all_buckets):
                        bucket = all_buckets[bucket_num - 1]
                except ValueError:
                    bucket = choice
            except (ValueError, IndexError):
                bucket = input("Enter bucket name: ").strip()
        else:
            bucket = input("Enter bucket name: ").strip()
    
    if not bucket:
        print("❌ Bucket name required")
        return False
    
    # Other settings with defaults
    prefix = input(f"Prefix [{config.config['default_prefix']}]: ").strip() or config.config['default_prefix']
    
    max_size_input = input(f"Max file size in MB [{config.config['default_max_size_mb']}]: ").strip()
    max_size_mb = int(max_size_input) if max_size_input else config.config['default_max_size_mb']
    
    expiration_input = input(f"Expiration in hours [{config.config['default_expiration_hours']}]: ").strip()
    expiration_hours = float(expiration_input) if expiration_input else config.config['default_expiration_hours']
    
    allowed_types_input = input("Allowed file types (comma-separated, e.g., image/*,video/*) [all]: ").strip()
    allowed_types = [t.strip() for t in allowed_types_input.split(',')] if allowed_types_input else None
    
    try:
        # Create S3 client
        client = S3DropClient(config.config['default_region'], config.config['verify_ssl'])
        
        # Check if bucket exists
        print(f"\n🔍 Checking bucket: {bucket}")
        if not client.bucket_exists(bucket):
            print(f"❌ Bucket '{bucket}' not found or not accessible")
            return False
        
        # Check CORS
        print(f"🔍 Checking CORS configuration...")
        has_cors = client.check_cors(bucket)
        if not has_cors:
            print(f"⚠️  CORS not configured for bucket '{bucket}'")
            setup_cors = input("Set up CORS now? (Y/n): ").strip().lower()
            if setup_cors != 'n':
                print(f"🔧 Setting up CORS...")
                if client.setup_cors(bucket):
                    print(f"✅ CORS configured successfully!")
                else:
                    print(f"❌ Failed to set up CORS. You may need to configure it manually.")
                    print(f"💡 See the documentation for CORS configuration instructions.")
        else:
            print(f"✅ CORS is configured")
        
        # Generate presigned POST
        print(f"🚀 Generating upload form...")
        
        expiration_seconds = int(expiration_hours * 3600)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        presigned_post = client.generate_presigned_post(
            bucket=bucket,
            prefix=prefix,
            max_size_bytes=max_size_bytes,
            allowed_types=allowed_types,
            expiration_seconds=expiration_seconds
        )
        
        # Generate HTML
        config_data = {
            'bucket': bucket,
            'prefix': prefix,
            'max_size_mb': max_size_mb,
            'expiration_hours': expiration_hours,
            'allowed_types': allowed_types
        }
        
        html_content = generate_upload_html(presigned_post, config_data)
        
        # Save HTML file
        timestamp = int(time.time())
        filename = f"s3drop-upload-{bucket}-{timestamp}.html"
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        print(f"\n✅ Upload form generated successfully!")
        print(f"📄 File: {filename}")
        print(f"🌍 Bucket: {bucket}")
        if prefix:
            print(f"📁 Prefix: {prefix}")
        print(f"📏 Max size: {format_file_size(max_size_bytes)}")
        print(f"⏰ Expires: {format_duration(expiration_seconds)}")
        if allowed_types:
            print(f"🎯 File types: {', '.join(allowed_types)}")
        
        print(f"\n🎉 Share this HTML file with users to upload files!")
        
        # Add to history
        config.add_to_history('upload-form', bucket, {
            'prefix': prefix,
            'max_size_mb': max_size_mb,
            'expiration_hours': expiration_hours,
            'filename': filename
        })
        
        # Add to favorites if not already there
        if bucket not in config.config['favorite_buckets']:
            add_fav = input(f"\nAdd '{bucket}' to favorites? (y/N): ").strip().lower()
            if add_fav == 'y':
                config.add_favorite_bucket(bucket)
                print(f"⭐ Added to favorites")
        
        return True
        
    except NoCredentialsError:
        print(f"❌ AWS credentials not found")
        print(f"💡 Configure AWS credentials using: aws configure")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ AWS Error ({error_code}): {error_msg}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def interactive_download_url(config: S3DropConfig):
    """Interactive download URL generation with improved UX."""
    print(f"\n📥 Generate Download URL")
    print("=" * 50)
    
    # Bucket selection (same as upload form)
    bucket = config.config['default_bucket']
    if not bucket or input(f"Use default bucket '{bucket}'? (Y/n): ").strip().lower() == 'n':
        # Show available buckets
        buckets = list_buckets(config)
        favorites = config.config['favorite_buckets']
        
        all_buckets = []
        if favorites:
            print(f"\n⭐ Favorite buckets:")
            for i, fav_bucket in enumerate(favorites, 1):
                print(f"   {i}. {fav_bucket}")
                all_buckets.append(fav_bucket)
        
        if buckets:
            start_num = len(favorites) + 1
            print(f"\n📋 Available buckets:")
            for i, available_bucket in enumerate(buckets, start_num):
                if available_bucket not in favorites:
                    print(f"   {i}. {available_bucket}")
                    all_buckets.append(available_bucket)
        
        if all_buckets:
            try:
                choice = input(f"\nSelect bucket (number or name): ").strip()
                try:
                    bucket_num = int(choice)
                    if 1 <= bucket_num <= len(all_buckets):
                        bucket = all_buckets[bucket_num - 1]
                except ValueError:
                    bucket = choice
            except (ValueError, IndexError):
                bucket = input("Enter bucket name: ").strip()
        else:
            bucket = input("Enter bucket name: ").strip()
    
    if not bucket:
        print("❌ Bucket name required")
        return False
    
    try:
        # Create S3 client
        client = S3DropClient(config.config['default_region'], config.config['verify_ssl'])
        
        # Check if bucket exists
        print(f"\n🔍 Checking bucket: {bucket}")
        if not client.bucket_exists(bucket):
            print(f"❌ Bucket '{bucket}' not found or not accessible")
            return False
        
        # Browse files in bucket
        print(f"🔍 Loading files from bucket...")
        current_prefix = ""
        
        while True:
            # List folders and files
            prefixes = client.list_prefixes(bucket, current_prefix)
            objects = client.list_objects(bucket, current_prefix, max_keys=50)
            
            print(f"\n📁 Current location: s3://{bucket}/{current_prefix}")
            print("=" * 60)
            
            options = []
            option_num = 1
            
            # Add back/up option if not at root
            if current_prefix:
                print(f"   {option_num}. 📂 .. (go back)")
                options.append(('back', ''))
                option_num += 1
            
            # Add folders
            for prefix in prefixes:
                folder_name = prefix[len(current_prefix):].rstrip('/')
                print(f"   {option_num}. 📂 {folder_name}/")
                options.append(('folder', prefix))
                option_num += 1
            
            # Add files
            for obj in objects:
                if obj['key'] != current_prefix:  # Skip folder itself
                    file_name = obj['key'][len(current_prefix):]
                    if '/' not in file_name:  # Only immediate files, not nested
                        size_str = format_file_size(obj['size'])
                        modified_str = obj['modified'].strftime('%m/%d/%Y')
                        print(f"   {option_num}. 📄 {file_name} ({size_str}, {modified_str})")
                        options.append(('file', obj['key']))
                        option_num += 1
            
            if not options:
                print("   (empty)")
            
            print(f"\n💡 Options:")
            print(f"   m. Enter file path manually")
            print(f"   r. Refresh")
            print(f"   q. Cancel")
            
            try:
                choice = input(f"\nSelect option: ").strip().lower()
                
                if choice == 'q':
                    print("👋 Cancelled")
                    return False
                elif choice == 'r':
                    continue
                elif choice == 'm':
                    key = input("Enter file path/key: ").strip()
                    if key:
                        break
                    else:
                        print("❌ File path required")
                        continue
                else:
                    try:
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(options):
                            option_type, option_value = options[choice_num - 1]
                            
                            if option_type == 'back':
                                # Go back one level
                                if '/' in current_prefix.rstrip('/'):
                                    current_prefix = '/'.join(current_prefix.rstrip('/').split('/')[:-1]) + '/'
                                else:
                                    current_prefix = ""
                            elif option_type == 'folder':
                                current_prefix = option_value
                            elif option_type == 'file':
                                key = option_value
                                break
                        else:
                            print("❌ Invalid option number")
                    except ValueError:
                        print("❌ Please enter a valid number or option")
                        
            except KeyboardInterrupt:
                print("\n👋 Cancelled")
                return False
        
        # Expiration
        expiration_input = input(f"\nExpiration in hours [{config.config['default_expiration_hours']}]: ").strip()
        expiration_hours = float(expiration_input) if expiration_input else config.config['default_expiration_hours']
        
        # Generate presigned URL
        print(f"\n🚀 Generating download URL...")
        
        expiration_seconds = int(expiration_hours * 3600)
        expiration_time = datetime.now() + timedelta(hours=expiration_hours)
        
        download_url = client.generate_presigned_url(
            bucket=bucket,
            key=key,
            expiration_seconds=expiration_seconds,
            method='get_object'
        )
        
        # Create output file
        timestamp = int(time.time())
        filename = f"s3drop-download-{bucket.replace('/', '-')}-{timestamp}.html"
        
        html_content = generate_download_instructions(download_url, bucket, key, expiration_time)
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        print(f"\n✅ Download URL generated successfully!")
        print(f"📄 Instructions file: {filename}")
        print(f"🌍 Bucket: {bucket}")
        print(f"📁 File: {key}")
        print(f"⏰ Expires: {expiration_time.strftime('%B %d, %Y at %I:%M %p')}")
        print(f"\n🔗 Direct URL:")
        print(f"   {download_url[:80]}...")
        print(f"\n🎉 Open the HTML file for easy downloading and sharing!")
        
        # Add to history
        config.add_to_history('download', bucket, {
            'key': key,
            'expiration_hours': expiration_hours,
            'filename': filename,
            'url': download_url[:100] + '...'  # Truncate for history
        })
        
        # Add to favorites if not already there
        if bucket not in config.config['favorite_buckets']:
            add_fav = input(f"\nAdd '{bucket}' to favorites? (y/N): ").strip().lower()
            if add_fav == 'y':
                config.add_favorite_bucket(bucket)
                print(f"⭐ Added to favorites")
        
        return True
        
    except NoCredentialsError:
        print(f"❌ AWS credentials not found")
        print(f"💡 Configure AWS credentials using: aws configure")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ AWS Error ({error_code}): {error_msg}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def interactive_mode():
    """Main interactive mode."""
    config = S3DropConfig()
    
    while True:
        try:
            print(f"\n🚀 S3-Drop v{VERSION}")
            print("=" * 50)
            
            # Show current config briefly
            if config.config['default_bucket']:
                print(f"📍 Default bucket: {config.config['default_bucket']}")
            else:
                print(f"📍 No default bucket configured")
            
            print(f"🌍 Region: {config.config['default_region']}")
            
            print(f"\n🎯 What would you like to do?")
            print(f"   1. 📤 Generate upload form")
            print(f"   2. 📥 Generate download URL")
            print(f"   3. 🔧 Configure settings")
            print(f"   4. 📋 View recent operations")
            print(f"   5. ⭐ View current config")
            print(f"   r. Refresh")
            print(f"   q. Quit")
            
            choice = input(f"\nSelect option: ").strip().lower()
            
            if choice == 'q':
                print(f"👋 Thanks for using S3-Drop!")
                break
            elif choice == '1':
                interactive_upload_form(config)
            elif choice == '2':
                interactive_download_url(config)
            elif choice == '3':
                configure_settings(config)
            elif choice == '4':
                show_recent_history(config)
            elif choice == '5':
                show_current_config(config)
            elif choice == 'r':
                print(f"🔄 Refreshed!")
                continue
            else:
                print(f"❌ Invalid option. Please try again.")
                input(f"Press Enter to continue...")
                
        except KeyboardInterrupt:
            print(f"\n👋 Thanks for using S3-Drop!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            input(f"Press Enter to continue...")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="S3-Drop - Professional S3 presigned URL generator",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=f"""Examples:
  s3drop                           # Interactive mode (recommended)
  s3drop upload-form               # Quick upload form generation
  s3drop download                  # Quick download URL generation
  s3drop config                    # Configure settings
  s3drop history                   # View recent operations

Interactive Mode:
  The default interactive mode provides a menu-driven interface
  for generating upload forms and download URLs with full configuration.

Quick Commands:
  For automation and scripting, use the direct commands with options.
        """
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'S3-Drop v{VERSION}'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands'
    )
    
    # Upload form command
    upload_parser = subparsers.add_parser(
        'upload-form',
        help='Generate upload form'
    )
    upload_parser.add_argument('--bucket', '-b', help='S3 bucket name')
    upload_parser.add_argument('--prefix', '-p', help='File prefix/folder')
    upload_parser.add_argument('--max-size', '-s', type=int, help='Max file size (MB)')
    upload_parser.add_argument('--expiration', '-e', type=float, help='Expiration (hours)')
    upload_parser.add_argument('--types', '-t', help='Allowed file types (comma-separated)')
    upload_parser.add_argument('--region', '-r', help='AWS region')
    upload_parser.add_argument('--no-ssl', action='store_true', help='Disable SSL verification')
    
    # Download command
    download_parser = subparsers.add_parser(
        'download',
        help='Generate download URL'
    )
    download_parser.add_argument('--bucket', '-b', help='S3 bucket name')
    download_parser.add_argument('--key', '-k', help='S3 object key')
    download_parser.add_argument('--expiration', '-e', type=float, help='Expiration (hours)')
    download_parser.add_argument('--region', '-r', help='AWS region')
    download_parser.add_argument('--no-ssl', action='store_true', help='Disable SSL verification')
    
    # Config command
    config_parser = subparsers.add_parser(
        'config',
        help='Configure settings'
    )
    
    # History command
    history_parser = subparsers.add_parser(
        'history',
        help='View recent operations'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'upload-form':
        # TODO: Implement direct upload form generation
        print("📤 Direct upload form generation coming soon!")
        print("💡 Use interactive mode: s3drop")
    elif args.command == 'download':
        # TODO: Implement direct download URL generation
        print("📥 Direct download URL generation coming soon!")
        print("💡 Use interactive mode: s3drop")
    elif args.command == 'config':
        config = S3DropConfig()
        configure_settings(config)
    elif args.command == 'history':
        config = S3DropConfig()
        show_recent_history(config)
    else:
        # No command specified - run interactive mode
        try:
            interactive_mode()
        except KeyboardInterrupt:
            print(f"\n👋 Thanks for using S3-Drop!")
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()