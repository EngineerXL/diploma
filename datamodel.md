# Модель данных

## Модель данных в PostgreSQL

```plantuml
@startuml
class OrgTreeEdge {
  -bigint id
  -bigint id_u
  -bigint id_v
  -boolean parent
  -text date
}

class OrgTreeNode {
  -bigint id
  -text type
  -bigint object_id
  -text date
}

class OrgUnit {
  -bigint id
  -text name   
  -text type
  -text json
  -text date
}

class Sensor{
 -bigint id
 -bigint type_id
 -bigint ch_id
 -text date
}

class SensorType{
  -bigint id
  -bigint freq
  -bigint dim
  -text info
}

OrgTreeNode --- OrgTreeEdge: "Связывает вершины\nдерева орг. структуры"

OrgTreeNode --- OrgUnit: "Вершина дерева\nописывает единицу\nорг. структуры"

OrgTreeNode --- Sensor: "Вершина дерева\nописывает сенсор"

Sensor -- SensorType: "Датчик типа"
@enduml
```
