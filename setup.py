import os
import re
import sys
from glob import glob
from setuptools import setup, find_packages

# Declare your non-python data files:
# Files underneath configuration/ will be copied into the build preserving the
# subdirectory structure if they exist.
data_files = []
for root, dirs, files in os.walk('config'):
    data_files.append((os.path.relpath(root, 'config'),
                       [os.path.join(root, f) for f in files]))
    
if "users_service" in sys.argv:
    scripts = ['bin/run_users_service.py']
    console_scripts = [
        "run-users-service=bin.run_users_service:main"
    ]
    app = "users-service"
    sys.argv.remove('users_service')

elif "onlinestore_service" in sys.argv:
    scripts = ['bin/run_onlinestore_service.py']
    console_scripts = [
        "run-onlinestore-service=bin.run_onlinestore_service:main"
    ]
    app = "onlinestore-service"
    sys.argv.remove('onlinestore_service')


setup(
        name=app,
        version="1.0",

        # declare your packages
        packages=find_packages(),
        # declare your scripts
        scripts=scripts,
        # include data files
        data_files=data_files,
        # entry points
        entry_points={
            "console_scripts": console_scripts
        }
    )
