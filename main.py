"""
Entry point to run the Django application with Replit
"""
import os
from django.core.wsgi import get_wsgi_application

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edplatform.settings')

# Initialize Django WSGI application
app = get_wsgi_application()

if __name__ == '__main__':
    # If run directly, start the development server
    from django.core.management import execute_from_command_line
    import sys
    
    # Set the binding host and port
    host = os.environ.get('HOST', '0.0.0.0')
    port = os.environ.get('PORT', '5000')
    
    # Run with runserver command
    sys.argv = [sys.argv[0], 'runserver', f'{host}:{port}']
    execute_from_command_line(sys.argv)
