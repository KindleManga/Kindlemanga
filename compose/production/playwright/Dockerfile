FROM mcr.microsoft.com/playwright/python:v1.28.0-focal

WORKDIR /root

COPY ./compose/production/playwright/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY ./compose/production/playwright/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/production/playwright/api_server.py ./api_server.py

ENTRYPOINT [ "/entrypoint" ]
