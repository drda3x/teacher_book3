
FROM ubuntu:16.04

RUN apt-get update 
RUN apt-get upgrade -y

RUN apt-get install -y curl

RUN apt-get install -y python-pip && pip install --upgrade
RUN apt-get install -y iputils-ping

RUN pip install django==1.8.2
RUN apt-get install -y libmysqlclient-dev
RUN pip install MySQL-python
RUN apt-get install -y mysql-client
RUN apt-get install -y vim-gnome
RUN pip install pytz

RUN curl -sL https://deb.nodesource.com/setup_8.x 
RUN apt-get install -y nodejs-legacy npm
RUN npm install -g bower
RUN npm install -g gulp && npm install gulp gulp-concat gulp-bower-files

RUN apt-get install -y git

CMD ["bash"]
