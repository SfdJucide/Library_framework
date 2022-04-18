
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

DROP TABLE IF EXISTS reader;
CREATE TABLE reader (
 id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
 first_name VARCHAR (32),
 last_name VARCHAR (32)
 );

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
