import sys

project_path = "/home/YOUR_USERNAME/cle-techfest"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from app import app as application
