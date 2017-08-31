linux setup with apache2 and ubuntu for python wsgi mod.

1. running updates.. - @in linux - initial setup
1.1 view pkg list   - $ cat /etc/apt/sources.list 
1.2 update pkg list - $ sudo apt-get update
1.3 to upgrade pkgs - $ sudo apt-get upgrade
1.4 automanage pkgs - $ sudo apt-get install unattended-upgrades
1.5 enable automngr - $ sudo dpkg-reconfigure --priority=low unattended-upgrades
1.6 config timezone - $ sudo dpkg-reconfigure tzdata
1.7 install ntp     - $ sudo apt-get install ntp ## network time sync

2. create a new super user..
2.1 install finger  - $ sudo apt-get install finger
2.2 add new user    - $ sudo adduser <name>
2.3 let user sudo   - $ usermod -aG sudo <name>
#2.3 alternatively  - $ sudo nano /etc/sudoers.d/<name> - "ALL=(ALL) ALL" ##save file
2.4 login new user  - $ su <name>
2.5 set root pswd   - $ sudo passwd root

3. setup rsa key auth - @on local machine.
3.1 create rsa keys - $ ssh-keygen ## save in /users/you/.ssh/your_key
3.2 copy pub key    - $ cat /users/you/.ssh/your_key.pub 
3.3 @linux as user  - $ nano .ssh/authorized_keys ## paste key, it should end with the name of the key.
3.4 secure files    - $ chmod 700 .ssh - $ chmod 644 .ssh/authorized_keys
3.5 disable passwds - $ sudo nano /etc/ssh/sshd_config ## change pwdauth to no and uncomment. 
3.6 change ssh port - change ssh port to 2200 in this ^ file and
3.7 dsbl root ssh   - change permitrootlogin to without-password or no
3.8 restart ssh     - $ sudo service ssh restart

4. configure firewall
4.0 apply defaults  - $ sudo ufw default deny incoming - $ sudo ufw default allow outgoing
4.1 allow ssh port  - $ sudo ufw allow 2200/tcp
4.2 allow www port  - $ sudo ufw allow 80/tcp
4.3 allow ntp port  - $ sudo ufw allow 123/udp
4.4 enable firewall - $ sudo ufw enable ## check status with - $ sudo ufw status

5. install apache2, python, mod_wsgi 
5.1 install apache2 - $ sudo apt-get install apache2
5.2 python & wsgi   - $ sudo apt-get install python-setuptools libapache2-mod-wsgi
5.3 enable wsgi     - $ sudo a2enmod wsgi
5.4 restart apache2 - $ sudo service apache2 restart

6. install postgresql and database
6.1 install postgre - $ sudo apt-get install  postgresql
6.2 change user     - $ su postgres
6.3 psql shell      - $ psql
6.4 create new db   - $ CREATE DATABASE <yourdbname>
6.5 create new user - $ CREATE USER <yourusername>
6.6 set user passwd - $ ALTER ROLE <yourusername> WITH PASSWORD "password"
6.7 set permissions - $ GRANT ALL PRIVILEGES ON DATABASE <yourdbname> TO <yourusername>
6.8 quit postgres   - $ \q ## then $ exit

7. clone git project repo
7.! update project files @ engine = create_engine('postgresql://<yourusername>:<youruserpass>@localhost/<yourdbname>')
7.1 install git     - $ sudo apt-get install git
7.2 config git name - $ git config --global user.name <name>
7.2 cnfgr git email - $ git config --global user.email <email>
7.3 change dir      - $ cd /var/www
7.4 clone git proj  - $ git clone proj-url-here appname
7.5 cd into project - $ cd /var/www/appname
7.5 rename app proj - $ sudo mv app.py __init__.py
7.6 install your db - $ this will be done in step 8.4 

8. install dependencies, python modules
8.1 install pip     - $ sudo apt-get install python-pip
8.2 install psycopg - $ sudo apt-get install python-psycopg2
8.3 install modules - $ sudo apt-get requests httplib2 flask-sqlalchemy flask ## and anything required for your app.
8.4 spawn database  - $ sudo python /var/www/appname/model.py  ## see /var/log/apache2/error.log for errors if any.

9. setup wsgi virtual host
9.1 mod config file - $ sudo nano /etc/apache2/sites-available/appname.conf
9.2 paste in template and configure it 













