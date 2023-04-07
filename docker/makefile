ch:
	clickhouse-client --port 25501 --user chuser --password chuser -d chdb

up:
	docker-compose up -d

down:
	docker-compose down

clean:
	docker volume ls
	docker volume rm docker_db-volume-ch
	docker volume rm docker_db-volume-pg

restart: down clean up
