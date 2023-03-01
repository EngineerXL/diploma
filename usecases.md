# Процессы по работе с данными

```plantuml
@startuml
left to right direction
skinparam packageStyle rect

actor admin

rectangle "Admin API" {
  admin -- (Create org tree edge)
  admin -- (Create org tree node)
  admin -- (Create new sensor type)
  admin -- (Redefine\nsensor properties)
  admin -- (Create new sensor)
  admin -- (Change sensor type)
  admin -- (Create new org unit)

' ?
  admin -- (publish schema\nto test environment)
' ?
  admin -- (publish schema\nto production environment)

'  (checkout) .> (payment) : include
'  (help) .> (checkout) : extends
'  (checkout) -> (authorize)
'  (checkout) -- clerk
}
@enduml
```
