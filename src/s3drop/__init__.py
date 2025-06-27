"""
S3-Drop - Professional S3 presigned URL generator with drag & drop HTML interfaces

A modern, user-friendly CLI tool for generating secure upload forms and download URLs
for Amazon S3. Features interactive menus, configuration management, and beautiful
HTML upload interfaces with drag & drop support.

Key Features:
- 🎯 Interactive mode with menu-driven interface
- 📤 Beautiful HTML upload forms with drag & drop
- 📥 Secure download URL generation
- 🔧 Configuration management and favorites
- 📋 Operation history tracking
- 🔒 Automatic CORS setup and verification
- ⚡ Fast, reliable, and secure

Usage:
    # Interactive mode (recommended)
    s3drop
    
    # Quick commands
    s3drop upload-form --bucket my-bucket --prefix uploads
    s3drop download --bucket my-bucket --key path/to/file.pdf
    
    # Configuration
    s3drop config

Example:
    from s3drop import S3DropClient, S3DropConfig
    
    config = S3DropConfig()
    client = S3DropClient(region='us-east-1')
    
    # Generate upload form
    presigned_post = client.generate_presigned_post(
        bucket='my-bucket',
        prefix='uploads',
        max_size_bytes=100*1024*1024  # 100MB
    )
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "Professional S3 presigned URL generator with drag & drop HTML interfaces"
__url__ = "https://github.com/yourusername/s3-drop"
__license__ = "MIT"

# Import main components for programmatic usage
try:
    from .cli import (
        S3DropClient,
        S3DropConfig,
        format_file_size,
        format_duration,
        generate_upload_html,
        main,
        interactive_mode,
        interactive_upload_form,
        interactive_download_url,
    )
except ImportError as e:
    # Graceful handling if dependencies are missing
    import sys
    print(f"Warning: Could not import s3drop components: {e}", file=sys.stderr)
    print("This might indicate missing dependencies. Try: pip install boto3", file=sys.stderr)
    
    # Define placeholder functions
    def main():
        """Placeholder main function - dependencies may be missing."""
        raise ImportError(f"s3drop dependencies missing: {e}")
    
    # Set other functions to None
    S3DropClient = S3DropConfig = format_file_size = format_duration = None
    generate_upload_html = interactive_mode = interactive_upload_form = None
    interactive_download_url = None

# Public API
__all__ = [
    # CLI entry point
    'main',
    
    # Core classes
    'S3DropClient',
    'S3DropConfig',
    
    # Utility functions
    'format_file_size',
    'format_duration',
    'generate_upload_html',
    
    # Interactive functions
    'interactive_mode',
    'interactive_upload_form',
    'interactive_download_url',
    
    # Metadata
    '__version__',
    '__author__',
    '__description__',
]

# Package metadata for introspection
__package_info__ = {
    'name': 's3-drop',
    'version': __version__,
    'author': __author__,
    'description': __description__,
    'url': __url__,
    'license': __license__,
    'python_requires': '>=3.7',
    'dependencies': ['boto3>=1.26.0'],
    'keywords': [
        'aws', 's3', 'presigned-url', 'file-upload', 'file-download',
        'cli', 'drag-drop', 'html-interface', 'cloud-storage'
    ],
}

def get_package_info():
    """Return package metadata as a dictionary."""
    return __package_info__.copy()

def print_version():
    """Print version information."""
    print(f"S3-Drop v{__version__}")
    print(f"Professional S3 presigned URL generator")
    print(f"Author: {__author__}")
    print(f"URL: {__url__}")

def print_help():
    """Print quick help information."""
    print(f"🚀 S3-Drop v{__version__}")
    print(f"Professional S3 presigned URL generator with HTML interfaces")
    print()
    print(f"Quick Start:")
    print(f"  s3drop                    # Interactive mode (recommended)")
    print(f"  s3drop upload-form        # Generate upload form")
    print(f"  s3drop download           # Generate download URL")
    print(f"  s3drop config             # Configure settings")
    print(f"  s3drop --help             # Full help")
    print()
    print(f"Features:")
    print(f"  🎯 Interactive menu-driven interface")
    print(f"  📤 Beautiful drag & drop upload forms")
    print(f"  📥 Secure download URLs with expiration")
    print(f"  🔧 Configuration management")
    print(f"  📋 Operation history tracking")
    print(f"  🔒 Automatic CORS setup")

# Add convenience functions to __all__
__all__.extend(['get_package_info', 'print_version', 'print_help'])

# Configuration for development
if __name__ == "__main__":
    print_help()