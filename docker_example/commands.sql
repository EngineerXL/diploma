CREATE TABLE OrgTreeEdges(
   id          bigserial   PRIMARY KEY,
   id_u        bigint      NOT NULL,
   id_v        bigint      NOT NULL,
   parent      boolean     NOT NULL   
);

CREATE TABLE OrgTreeNodes(
   id          bigserial   PRIMARY KEY,
   type        text        NOT NULL,
   object_id   bigint      NOT NULL
);

CREATE TABLE OrgUnits(
   id          bigserial   PRIMARY KEY,
   name        text,
   type        text,
   json        text
);

CREATE TABLE Sensors(
   id          bigserial   PRIMARY KEY,
   type_id     bigint      NOT NULL
);

CREATE TABLE SensorTypes(
   id          bigserial   PRIMARY KEY,
   freq        bigint      NOT NULL,
   dim         bigint      NOT NULL,
   info        text
);