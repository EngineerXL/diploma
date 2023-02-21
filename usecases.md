## Процессы по работе с данными

```plantuml

@startuml
left to right direction
skinparam packageStyle rect

actor admin

rectangle system {
  admin -- (create new sensor)
  admin -- (create org unit)
  admin -- (assign sensor to unit)
  admin -- (organize units into hierarchy)
  admin -- (redefine sensor property)

  admin -- (publish schema to test environment)
  admin -- (publish schema to production environment)
'  (checkout) .> (payment) : include
'  (help) .> (checkout) : extends
'  (checkout) -> (authorize)
'  (checkout) -- clerk
}
@enduml
```