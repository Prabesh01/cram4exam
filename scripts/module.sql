PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "app_module" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "code" varchar(10) NOT NULL UNIQUE, "name" varchar(255) NOT NULL, "year_long" bool NOT NULL, "year" integer NOT NULL, "sem" integer NOT NULL);
INSERT INTO app_module VALUES(1,'CC5051NP','Databases',0,2,1);
INSERT INTO app_module VALUES(2,'CS5053NP','Cloud Computing and Internet of Things',0,2,1);
INSERT INTO app_module VALUES(3,'CT5052NP','Network Operating Systems',0,2,1);
INSERT INTO app_module VALUES(4,'CS5002NP','Software Engineering',1,2,1);
INSERT INTO app_module VALUES(5,'CS5054NP','Advanced Programming and Technologies',0,2,2);
INSERT INTO app_module VALUES(6,'CC5067NP','Smart Data Discovery',0,2,2);
INSERT INTO app_module VALUES(7,'CS5052NP','Professional and Ethical Issues',0,2,2);
INSERT INTO app_module VALUES(8,'CT4005NP','Computer Hardware & Software Architectures',1,1,1);
INSERT INTO app_module VALUES(9,'CS4001NP','Programming',0,1,2);
INSERT INTO app_module VALUES(10,'CS4051NP','Fundamentals of Computing',0,1,1);
INSERT INTO app_module VALUES(11,'CC4057','Introduction to Information Systems',0,1,1);
INSERT INTO app_module VALUES(12,'MA4001','Logic and Problem Solving',1,1,1);
INSERT INTO app_module VALUES(13,'CS6004NP','Application Development',0,3,1);
INSERT INTO app_module VALUES(14,'CC6001NP','Advanced Database Systems Development',0,3,1);
INSERT INTO app_module VALUES(15,'CC6012NP','Data and Web Development',0,3,1);
COMMIT;
