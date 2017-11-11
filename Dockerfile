
FROM ubuntu:16.04
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python-pip && pip install --upgrade
RUN apt-get install -y iputils-ping
RUN pip install django==1.8.2
RUN apt-get install -y libmysqlclient-dev
RUN pip install MySQL-python
RUN apt-get install -y mysql-client
RUN apt-get install -y vim-gnome
RUN pip install pytz

RUN mkdir /app
COPY teacher_book /app

CMD ["bash"]
