# LeadsMgmt
###Steps Needed:
####git clone the repo

## For local setup.
Assuming you are /var/www/yoursite/
git clone the repo. Follow git documentation [here](https://www.atlassian.com/git/tutorials/atlassian-git-cheatsheet)
install python3 if not there.
- sudo yum install python3-pip
- install virtualenv and activate it. [Help](https://www.liquidweb.com/kb/how-to-setup-a-python-virtual-environment-on-centos/)

Now installing django project
-cd yourRepo
-pip install -r [requirements.txt](requirements.txt)

In the [settings.py](StrongerAB1/settings.py) make sure your connection is local sqlite.

If local DB:

- python manage.py makemigrations
- python manage.py migrate
- python manage.py runserver

Otherwise if you are connecting to other existing remote database, just only use :

-python manage.py runserver  
For any help, follow [here](https://docs.djangoproject.com/en/3.1/intro/tutorial01/)


You will see the below message if the server starts.
 
Django version 2.1.5, using settings 'LeadsMgmt1.settings'
Starting development server at http://127.0.0.1:8000/


##For production :
Create directory structure: /var/www/yoursite
cd /var/www/yoursite
Install python3 if not exists
- sudo yum install python3
- sudo yum install python3-pip
 * sudo pip3 install virtualenv
 
 Now git clone the repo.
 git clone https://bitbucket.org/sanjaydot3399/leadsmgmt/src/master/
 
- give enough permissions using below command
-sudo chmod . 777 -R
cd /var/www/yoursite/LeadsMgmt/

sudo su
- Create and activate virtual env at your project location
- "virtualenv venv"
- "source venv/bin/activate"
- "pip install gunicorn"
- "pip install -r [requirements.txt](requirements.txt)"
  
  Place the file ['gunicorn_start2'](useful_files) in the 'bin' directory of virtual env. 
 i.e - "cp useful_files/guinicorn_start2    venv/bin/"
 - copy the settings_prod to settings.py
  - cp LeadsMgmt/LeadsMgmt1/settings_prod.py LeadsMgmt/LeadsMgmt1/settings.py
  -Activate database changes using "python mangage.py migrate"
 
 - Start the gunicorn server using venv/bin/gunicorn_start2
 - To kill just just use "sudo pkill -9 gunicorn"
 
 
   ## Now the Production Nginx server steps:
    - sudo yum install epel-release
    - sudo yum install nginx
    - sudo systemctl start nginx
    - sudo systemctl enable nginx
    
    Look at the [nginx.conf](useful_files/nginx.conf) and make changes accordingly to nginx.conf file located in the nginx installation.

    Restart nginx server. 
    
    -  sudo systemctl restart  nginx
    
       Now access the application using the ip address of the server.
    
       try running command  "setenforce 0" if application loading fails.
    
    

   ## Postgresql Server Creation steps.
        Please follow the steps exactly [here](https://docs.cloudera.com/cem/1.1.0/installation/topics/cem-install-configure-postgres.html) to create DB and backup
  
        For congiguration, look at the [file](useful_files/postgreql.conf) and make chagnes at /var/lib/pgsql/data/pg_hba.conf 
  
        Just creating empty databse is enough for django application. All the schemas are created once you call
  
        Update DB connection details in [settings.py](LeadsMgmt1/settings.py)
  
        python manage.py migrate 
  
         For DB backup, Please look [at](useful_files/backupScript) and create cronjob .




 
 
 
 
 
 
 

###commands to run for deploying code changes in existing running server.
Please make required changes in those files if you want.
sudo su
- cd /var/www/yoursite/LeadMgmt

-git checkout branch and git pull

-copy the settings_prod to settings.py

-cp  LeadsMgmt1/settings_prod.py LeadsMgmt1/settings.py

-python manage.py migrate

Dont forget to give enough permission to logs/logfile if needed.

-sudo chmod 777 logs/logfile

kill the existing gunicorn process.
sudo pkill -9 gunicorn
start server script

sudo ven/bin/gunicorn_start2

You don't have touch any other files, restart any other servers.
FYI . Just look at the history of the commands in the server.



