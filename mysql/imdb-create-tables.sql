/*
This script creates the IMDb database tables.

Adapted from: https://github.com/dlwhittenbury/MySQL_IMDb_Project

To use the IMDb scripts:

1) Open MySQL in terminal:
 $ mysql -u root -p --local-infile IMDb

2) Create IMDb data base in MySQL:
 mysql> SOURCE /tmp/imdb-create-tables.sql

3) Load data using this script in MySQL:
 mysql> SOURCE  /tmp/imdb-load-data.sql

4) Add constraints to the IMDb database in MySQL
 mysql> SOURCE /tmp/imdb-add-constraints.sql

5) Add index to the IMDb database in MySQL
 mysql> SOURCE  /tmp/imdb-add-index.sql
*/

-- Delete IMDb database if necessary
DROP DATABASE IF EXISTS IMDb;

-- Create IMDb database

CREATE DATABASE IMDb;

-- Use IMDb database

USE IMDb;

-- Character set
-- want to be able to distinguish text with accents
ALTER DATABASE IMDb CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

-- Drop old tables if they exist

DROP TABLE IF EXISTS titles;
DROP TABLE IF EXISTS ratings;

DROP TABLE IF EXISTS episodes;
DROP TABLE IF EXISTS people;
DROP TABLE IF EXISTS crew;

-- Create tables only

CREATE TABLE titles (
  title_id 			  VARCHAR(255) NOT NULL, -- not null bc PK
  title_type 			VARCHAR(50),
  primary_title 	TEXT, 
  original_title 	TEXT, 
  is_adult 			  BOOLEAN,
  start_year			INTEGER, 
  end_year 			  INTEGER, 
  runtime_minutes	INTEGER, 
  genres VARCHAR(255) NOT NULL,
  PRIMARY KEY (title_id)
);

CREATE TABLE ratings (
  title_id 	VARCHAR(255) NOT NULL, -- not null bc PK
  rating	FLOAT,
  votes		INTEGER,
  PRIMARY KEY (title_id)
);


CREATE TABLE episodes (
  episode_title_id  VARCHAR(255) NOT NULL, -- not null bc PK
  show_title_id   VARCHAR(255) NOT NULL, -- fk to titles.title_id
  season_number   INTEGER,
  episode_number  INTEGER,
  PRIMARY KEY (episode_title_id)
);


CREATE TABLE people (
  person_id   VARCHAR(255) NOT NULL, -- not null bc PK
  person_name VARCHAR(255) NOT NULL, 
  born    SMALLINT, 
  died    SMALLINT,
  PRIMARY KEY (person_id) 
);

CREATE TABLE crew (
  title_id  VARCHAR(255) NOT NULL, -- not null bc PK
  person_id VARCHAR(255) NOT NULL, -- fk 
  category  VARCHAR(255),
  job       TEXT,
  show_characters VARCHAR(255),
  -- PRIMARY KEY (title_id, person_id, category, job, show_characters)
);
