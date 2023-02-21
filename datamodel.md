# Модель данных

## Модель данных в PostgreSQL
```plantuml
@startuml
class OrgGraph {
  -String id
  -String name
  -String type 
}

class OrgRelation{
  -String id
  -String name
}

class OrgUnitDescription{
  -String id
  -String name   
  -String type
  -String json
}

class Sensor{
 -String id
 -String type 
}

class SensorType{
    -String id
    -Int frequency
    -Int dimension
}

OrgGraph -- OrgRelation : родительская организация
OrgGraph -- OrgRelation : дочерняя организация

OrgGraph -- OrgUnitDescription : Описание организационной еденицы

Sensor -- OrgGraph : Установлен в цеху

Sensor -- SensorType: Является датчиком типа
@enduml
```

