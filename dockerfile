FROM python:3
RUN pip3 install requests --user

WORKDIR /usr/src/app

COPY . .

CMD [ "python3", "one_com_ddns.py" ]