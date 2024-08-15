### Installation
#### Create a virtual environment
- python -m venv world
#### Activate the virtual environment
- world/Scripts/activate (windows)
- source world/bin/activate (Max/Linux)
#### Install Dependencies 
- pip install -r requirements.txt
#### Unzip the File
#### Navigate to the Project Directory:
- cd spam_identifer
#### Apply Migrations
- python manage.py makemigrations
- python manage.py migrate
####  Run the Development Server
- python manage.py runserver
