# S3-Drop 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![AWS S3](https://img.shields.io/badge/AWS-S3-orange.svg)](https://aws.amazon.com/s3/)

**Professional S3 presigned URL generator with beautiful drag & drop HTML interfaces**

S3-Drop transforms the complex process of generating S3 presigned URLs into a delightful, interactive experience. Create secure upload forms and download links with just a few clicks.

## ✨ What It Does

- **📤 Upload Forms** - Generate beautiful HTML forms with drag & drop file upload
- **📥 Download URLs** - Create secure, time-limited download links
- **🔧 Smart Configuration** - Save your settings, favorite buckets, and preferences  
- **📋 History Tracking** - Keep track of all your generated URLs and forms
- **🔒 CORS Management** - Automatically detect and configure CORS settings
- **🎯 Interactive Mode** - Menu-driven interface that's actually enjoyable to use

## 🎬 Quick Demo

```bash
# Interactive mode with beautiful menus
$ s3drop
🚀 S3-Drop v1.0.0
==================================================
📍 Default bucket: my-upload-bucket
🌍 Region: us-east-1

🎯 What would you like to do?
   1. 📤 Generate upload form
   2. 📥 Generate download URL  
   3. 🔧 Configure settings
   4. 📋 View recent operations
   5. ⭐ View current config
   q. Quit

Select option: 1

# Result: Beautiful HTML form with drag & drop interface!
```

## 🚀 Installation

### Option 1: Install from GitHub (Recommended)
```bash
# Install latest version directly from GitHub
pip install git+https://github.com/sovangwidomski/s3drop.git

# Or install a specific version/tag
pip install git+https://github.com/sovangwidomski/s3drop.git@v1.0.0
```

### Option 2: Install from PyPI (Coming Soon)
```bash
pip install s3-drop
```

### Option 3: Install from Source (Development)
```bash
# Clone the repository
git clone https://github.com/sovangwidomski/s3drop.git
cd s3drop

# Install in development mode
pip install -e .
```

### Verify Installation
```bash
# Check version
s3drop --version

# Start interactive mode
s3drop
```

### Prerequisites
- **Python 3.7+** - Modern Python version
- **AWS Credentials** - Configured via AWS CLI, environment variables, or IAM roles
- **S3 Access** - Permissions to create presigned URLs

## ⚡ Quick Start

### First Time Setup
```bash
# Configure AWS credentials (if not already done)
aws configure

# Install S3-Drop
pip install git+https://github.com/sovangwidomski/s3drop.git

# Start S3-Drop interactive mode
s3drop

# Follow the menus to:
# 1. Set your default bucket
# 2. Generate your first upload form
# 3. Share the HTML file with users
```

### 30-Second Upload Form
```bash
s3drop
# Select: 1. Generate upload form
# Enter: your-bucket-name
# Press Enter for defaults
# 🎉 Done! Beautiful upload form generated
```

## 🎯 Features Deep Dive

### 📤 Upload Forms
Generate stunning HTML upload interfaces:

- **Drag & Drop** - Modern file selection experience
- **Progress Tracking** - Real-time upload progress bars
- **File Validation** - Client-side size and type checking
- **Custom Styling** - Professional, responsive design
- **Security** - Direct-to-S3 uploads, no server required
- **Upload History** - Persistent confirmation and file tracking
- **Mobile Friendly** - Works perfectly on phones and tablets

**Example upload form features:**
- 5GB default file size limit (configurable)
- File type restrictions (images, documents, etc.)
- Custom expiration times
- Organized folder prefixes
- Celebration animations and success confirmation

### 📥 Download URLs
Create secure download links:

- **Time-Limited** - Configurable expiration (1 hour to 7 days)
- **Direct Access** - No authentication required for recipients
- **Audit Trail** - Track when URLs were generated
- **Bulk Generation** - Create multiple URLs efficiently

### 🔧 Smart Configuration
Never repeat yourself:

- **Default Settings** - Set your preferred bucket, region, file sizes
- **Favorite Buckets** - Quick access to frequently used buckets
- **Auto-Save** - Your preferences persist between sessions
- **Environment Detection** - Automatically detect AWS configuration

### 📋 History & Analytics
Keep track of everything:

- **Operation History** - See all generated URLs and forms
- **Usage Patterns** - Understand your most common operations
- **Quick Regeneration** - Easily recreate previous configurations
- **Export Options** - Save history for reporting

### 🔒 Security Features
Built with security in mind:

- **CORS Auto-Setup** - Automatically configure bucket CORS
- **Least Privilege** - Only requests necessary S3 permissions
- **No Credentials Storage** - Uses your existing AWS configuration
- **Time-Limited URLs** - All URLs expire automatically
- **SSL Verification** - Optional SSL verification control

## 📖 Usage Guide

### Interactive Mode (Recommended)

The default interactive mode provides a menu-driven interface:

```bash
s3drop
```

**Main Menu Options:**
1. **📤 Generate upload form** - Create HTML upload interfaces
2. **📥 Generate download URL** - Generate secure download links
3. **🔧 Configure settings** - Manage preferences and defaults
4. **📋 View recent operations** - See your operation history
5. **⭐ View current config** - Display current configuration

### Upload Form Generation

**Step-by-step process:**
1. Select bucket (from favorites or available buckets)
2. Choose folder prefix (e.g., "uploads/2025")
3. Set file size limit (default: 5GB)
4. Configure expiration time (default: 1 hour)
5. Optionally restrict file types
6. **Result:** Beautiful HTML file ready to share

**Generated HTML features:**
- Professional drag & drop interface
- Real-time upload progress
- Client-side file validation
- Mobile-responsive design
- Direct S3 upload (secure)
- Upload history tracking
- Success confirmation that persists

### Download URL Generation

**Quick process:**
1. Select bucket
2. Enter file path/key
3. Set expiration time
4. **Result:** Secure, shareable download URL

### Configuration Management

**Configure once, use everywhere:**
- Default bucket and region
- Preferred file size limits
- Standard expiration times
- Favorite buckets list
- SSL verification settings

## 💡 Common Use Cases

### Client File Collection
```bash
# Generate upload form for client project files
s3drop
# 1. Generate upload form
# Bucket: client-projects
# Prefix: project-alpha/deliverables
# Max size: 2GB
# Expires: 1 week
# File types: PDF, images only
```

### Team Document Sharing
```bash
# Quick download link for team documents
s3drop
# 2. Generate download URL
# Bucket: team-documents
# File: reports/q4-summary.pdf
# Expires: 24 hours
```

### Event Photo Collection
```bash
# Photo upload form for event attendees
s3drop
# 1. Generate upload form
# Bucket: event-photos
# Prefix: wedding-2025/guest-photos
# Max size: 500MB
# File types: image/* only
# Expires: 3 days
```

### Secure File Distribution
```bash
# Distribute confidential files securely
s3drop
# 2. Generate download URL
# Bucket: confidential-docs
# File: contracts/nda-template.pdf
# Expires: 2 hours
```

## 🛠️ Configuration

### Default Settings
S3-Drop saves your preferences in `~/.s3drop/config.json`:

```json
{
  "default_bucket": "my-upload-bucket",
  "default_region": "us-east-1",
  "default_prefix": "uploads",
  "default_max_size_mb": 5120,
  "default_expiration_hours": 1,
  "verify_ssl": true,
  "favorite_buckets": [
    "my-upload-bucket",
    "client-projects",
    "team-documents"
  ]
}
```

### Environment Variables
You can also configure via environment variables:

```bash
export AWS_REGION=us-west-2
export AWS_PROFILE=production
export S3DROP_DEFAULT_BUCKET=my-bucket
```

### AWS Credentials
S3-Drop uses your existing AWS configuration:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Option 3: IAM roles (EC2/Lambda)
# Automatically detected
```

## 🔧 Advanced Usage

### Command Line Interface
For automation and scripting:

```bash
# Generate upload form (non-interactive)
s3drop upload-form --bucket my-bucket --prefix uploads --max-size 1024

# Generate download URL (non-interactive)  
s3drop download --bucket my-bucket --key path/to/file.pdf --expiration 24

# Configure settings
s3drop config

# View operation history
s3drop history
```

### Programmatic Usage
Use S3-Drop as a Python library:

```python
from s3drop import S3DropClient, S3DropConfig

# Create client
config = S3DropConfig()
client = S3DropClient(region='us-east-1')

# Generate presigned POST for uploads
presigned_post = client.generate_presigned_post(
    bucket='my-bucket',
    prefix='uploads',
    max_size_bytes=100*1024*1024,  # 100MB
    expiration_seconds=3600
)

# Generate presigned URL for downloads
download_url = client.generate_presigned_url(
    bucket='my-bucket',
    key='path/to/file.pdf',
    expiration_seconds=3600
)
```

### Batch Operations
Generate multiple URLs efficiently:

```python
from s3drop import S3DropClient

client = S3DropClient()

# Generate download URLs for multiple files
files = ['doc1.pdf', 'doc2.pdf', 'doc3.pdf']
urls = []

for file in files:
    url = client.generate_presigned_url(
        bucket='my-bucket',
        key=f'documents/{file}',
        expiration_seconds=86400  # 24 hours
    )
    urls.append(url)
    print(f"✅ {file}: {url}")
```

## 🔒 Security Best Practices

### Bucket Configuration
**Required: CORS Setup**
S3-Drop can automatically configure CORS, or you can set it manually:

```json
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "POST", "PUT"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": [],
            "MaxAgeSeconds": 3600
        }
    ]
}
```

**Recommended: Bucket Policy**
Restrict uploads to presigned URLs only:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPresignedUploads",
            "Effect": "Allow", 
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::your-bucket/*"
        }
    ]
}
```

### Security Guidelines

**✅ Do:**
- Set appropriate expiration times (shorter = more secure)
- Use file type restrictions when possible
- Monitor your S3 access logs
- Use folder prefixes to organize uploads
- Enable S3 server-side encryption
- Regularly audit generated URLs

**❌ Don't:**
- Share presigned URLs in public places
- Set extremely long expiration times
- Allow unrestricted file sizes
- Skip CORS configuration
- Use weak AWS credentials

### File Size Recommendations

| Use Case | Recommended Limit | Reasoning |
|----------|-------------------|-----------|
| **Documents** | 100MB | PDFs, presentations, spreadsheets |
| **Images** | 500MB | Photos, graphics, design files |
| **General Purpose** | 5GB | Good balance of functionality and reliability |
| **Large Media** | 20GB | Videos, datasets (fast connections only) |
| **Enterprise** | 50GB+ | Internal use with managed networks |

## 🐛 Troubleshooting

### Common Issues

**CORS Errors**
```
Access to XMLHttpRequest blocked by CORS policy
```
**Solution:** S3-Drop can automatically set up CORS for you, or configure manually (see Security section).

**AWS Credentials Not Found**
```
NoCredentialsError: Unable to locate credentials
```
**Solution:** Configure AWS credentials using `aws configure` or environment variables.

**Bucket Access Denied**
```
AccessDenied: User is not authorized to perform: s3:PutObject
```
**Solution:** Ensure your AWS user/role has S3 permissions for the target bucket.

**SSL Certificate Issues**
```
SSL: CERTIFICATE_VERIFY_FAILED
```
**Solution:** Use the `--no-ssl` flag or configure SSL verification in settings.

### Debug Mode
Enable verbose output for troubleshooting:

```bash
export S3DROP_DEBUG=1
s3drop
```

### Getting Help
If you encounter issues:

1. **Check AWS credentials:** `aws sts get-caller-identity`
2. **Verify bucket access:** `aws s3 ls s3://your-bucket`
3. **Test basic S3 operations:** `aws s3 cp test.txt s3://your-bucket/`
4. **Review S3-Drop logs:** Check `~/.s3drop/` directory

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup
```bash
# Clone repository
git clone https://github.com/sovangwidomski/s3drop.git
cd s3drop

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Format code
black src/
```

### Project Structure
```
s3drop/
├── src/s3drop/           # Main package
│   ├── __init__.py       # Package initialization
│   └── cli.py            # CLI implementation
├── tests/                # Test suite
├── examples/             # Example configurations
├── README.md             # This file
├── setup.py              # Package configuration
└── requirements.txt      # Dependencies
```

### Contribution Guidelines
- **Code Quality:** Use black for formatting, write tests for new features
- **Documentation:** Update README and docstrings for changes
- **Compatibility:** Support Python 3.7+ and recent boto3 versions
- **Security:** Follow AWS security best practices

## 🔄 Changelog

### v1.0.0 (2025-01-XX)
- 🎉 **Initial release**
- ✅ **Interactive mode** with menu-driven interface
- ✅ **Upload form generation** with beautiful HTML interfaces
- ✅ **Download URL generation** with configurable expiration
- ✅ **Configuration management** with persistent settings
- ✅ **History tracking** for all operations
- ✅ **CORS auto-setup** and verification
- ✅ **Favorite buckets** management
- ✅ **Professional CLI** with emojis and clear feedback
- ✅ **Persistent success confirmation** with upload history
- ✅ **Mobile-responsive** upload forms

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AWS S3** - For providing the robust cloud storage platform
- **boto3** - For the excellent Python AWS SDK
- **Click/Argparse** - For CLI framework inspiration
- **The Python Community** - For amazing tools and libraries

---

**⭐ If S3-Drop makes your file sharing easier, please star the repository!**

**🐛 Found a bug or have a feature request? [Open an issue](https://github.com/sovangwidomski/s3drop/issues)**

**💬 Questions? [Start a discussion](https://github.com/sovangwidomski/s3drop/discussions)**