# Sensor types
curl -X 'POST' \
  'http://localhost:8080/SensorTypes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "freq": 2,
  "dim": 1,
  "info": "t1"
}'

curl -X 'POST' \
  'http://localhost:8080/SensorTypes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "freq": 3,
  "dim": 1,
  "info": "t2"
}'

curl -X 'POST' \
  'http://localhost:8080/SensorTypes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "freq": 5,
  "dim": 4,
  "info": "t3"
}'

curl -X 'POST' \
  'http://localhost:8080/SensorTypes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "freq": 7,
  "dim": 3,
  "info": "t4"
}'

curl -X 'POST' \
  'http://localhost:8080/SensorTypes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "freq": 2,
  "dim": 2,
  "info": "t5"
}'

# Sensors
curl -X 'POST' \
  'http://localhost:8080/Sensors' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type_id": 1,
  "chid": 1,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/Sensors' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type_id": 2,
  "chid": 2,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/Sensors' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type_id": 3,
  "chid": 3,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/Sensors' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type_id": 4,
  "chid": 4,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/Sensors' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type_id": 5,
  "chid": 5,
  "date": "2023-03-24"
}'

# Sensor nodes
curl -X 'POST' \
  'http://localhost:8080/OrgTreeNodes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type": "sensor",
  "object_id": 1,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeNodes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type": "sensor",
  "object_id": 2,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeNodes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type": "sensor",
  "object_id": 3,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeNodes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type": "sensor",
  "object_id": 4,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeNodes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type": "sensor",
  "object_id": 5,
  "date": "2023-03-24"
}'

# Org units
curl -X 'POST' \
  'http://localhost:8080/OrgUnits' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "name": "orgunit 1",
  "type": "some type 1",
  "json": "some json 1",
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgUnits' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "name": "orgunit 2",
  "type": "some type 2",
  "json": "some json 2",
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgUnits' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "name": "orgunit 3",
  "type": "some type 3",
  "json": "some json 3",
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgUnits' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "name": "orgunit 4",
  "type": "some type 4",
  "json": "some json 4",
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgUnits' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "name": "orgunit 5",
  "type": "some type 5",
  "json": "some json 5",
  "date": "2023-03-24"
}'

# Org unit nodes
curl -X 'POST' \
  'http://localhost:8080/OrgTreeNodes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type": "orgunit",
  "object_id": 1,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeNodes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type": "orgunit",
  "object_id": 2,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeNodes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type": "orgunit",
  "object_id": 3,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeNodes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type": "orgunit",
  "object_id": 4,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeNodes' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "type": "orgunit",
  "object_id": 5,
  "date": "2023-03-24"
}'

# Edges
curl -X 'POST' \
  'http://localhost:8080/OrgTreeEdges' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "id_u": 6,
  "id_v": 1,
  "parent": true,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeEdges' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "id_u": 6,
  "id_v": 2,
  "parent": true,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeEdges' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "id_u": 7,
  "id_v": 6,
  "parent": true,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeEdges' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "id_u": 7,
  "id_v": 9,
  "parent": true,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeEdges' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "id_u": 9,
  "id_v": 8,
  "parent": true,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeEdges' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "id_u": 9,
  "id_v": 3,
  "parent": true,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeEdges' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "id_u": 8,
  "id_v": 4,
  "parent": true,
  "date": "2023-03-24"
}'

curl -X 'POST' \
  'http://localhost:8080/OrgTreeEdges' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": 0,
  "id_u": 10,
  "id_v": 5,
  "parent": true,
  "date": "2023-03-24"
}'

