FROM mysql:8.0

# Устанавливаем переменные окружения
ENV MYSQL_ROOT_PASSWORD=123
ENV MYSQL_DATABASE=us_data
ENV MYSQL_USER=user
ENV MYSQL_PASSWORD=123

# Копируем скрипт инициализации базы данных в контейнер
COPY init.sql /docker-entrypoint-initdb.d/