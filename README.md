### Описание:
**FOODgram** - веб-сервис для любителей вкусно покушать. Вы сможете делиться рецептами с  фотографиями, добавлять к ним ингриденты, а также посмотреть, сохранить в избранном рецепты и скачать список необходимых продуктов для приготовления.

## Запуск проекта на сервере:

1. На GitHub форкнуть и клонировать репозиторий:
    ```
    git@github.com:Lif-a-nova/foodgram.git
    ```
2. Создать и активировать виртуальное окружение:
    ```
    python -m venv venv
    source venv/bin/activate
    ```
3. Создать необходимый файл с секретами .env (в корне проекта).
4. Собрать и сбилдить образы на свой DockerHub (из корня проекта):
     ```
    cd frontend
    docker build -t "username"/foodgram_frontend .
    cd ../backend
    docker build -t "username"/foodgram_backend .

    docker push "username"/foodgram_frontend
    docker push "username"/foodgram_backend
    ```
5. Развернуть на рабочем сервере ОС на ядре Linux. 
    (В проекте использовалась серверная версия ОС [Ubuntu](https://ubuntu.com/download/desktop) )
6. На сервере выполнить следующее:
    -- Nginx:
    Установить Nginx на сервер:
     ```
    sudo apt install nginx -y 
    - изменить настройки с учетом своего ip и проксирования:
    sudo nano /etc/nginx/sites-enabled/default
    - проверить файл конфигурации на ошибки:
    sudo nginx -t 	
    sudo systemctl start nginx
    ```
    -- Установить и запустит файрвол:
    ```
    sudo ufw allow 'Nginx Full'
    sudo ufw allow OpenSSH
    sudo ufw enable
    sudo ufw status 
    ```
    -- Docker
    Установить Docker и Docker Compose на сервер:
    ```
    sudo apt update
    sudo apt install curl
    curl -fSL https://get.docker.com -o get-docker.sh
    sudo sh ./get-docker.sh
    sudo apt-get install docker-compose-plugin
    ```
    -- Создать в корне каталога пустую дирректорию проекта:
     ```
    sudo mkdir foodgram
    cd foodgram
    - скопировать любым удобным образом 2 файла проекта из папки infra: 
    docker-compose.production.yml , nginx.conf 
    - фаил .env создать по примеру .env.example и тоже скопировать туда же
    ```
    -- Запустить в режиме «демона» файл docker-compose.production.yml:
    ```
    sudo docker compose -f docker-compose.production.yml up -d
    - подождать
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py makemigrations
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
    sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /app/static/
    sudo docker compose -f docker-compose.production.yml exec -ti backend python manage.py import_data_csv
    sudo docker compose -f docker-compose.production.yml exec -ti backend python manage.py create_superuser
    ```
    -- Перезагрузить конфигурацию Nginx:
    - предварительно прописав необходимый
    sudo nano /etc/nginx/sites-enabled/default
     и получить cerbot
    ```
    sudo systemctl reload nginx
    ```
7. Не забыть:
    ```
    Пользоваться с удовольствием!
    ```
