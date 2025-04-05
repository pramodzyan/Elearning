#!/bin/bash
# # set some environmental variables # NOT WORKING
# cat set_env.sh | /bin/bash;

# activate the virtual environment
source venv/bin/activate;

# install dependencies
pip install -r requirements.txt;

# migrate the database
python manage.py migrate;

# collect static files
python manage.py collectstatic --clear --noinput;

# import menu data
python manage.py Import_Menu_Data;

