/*
/*
This script loads normalised IMDb data into IMDb database tables created by
using the script imdb-create-tables.sql.

Adapted from: https://github.com/dlwhittenbury/MySQL_IMDb_Project

To use the IMDb scripts:

1) Open MySQL in terminal:
 $ mysql -u root -p --local-infile IMDb

2) Load data using this script in MySQL:
 mysql> SOURCE  /tmp/imdb-load-data.sql
 
*/


-- SHOW VARIABLES LIKE "local_infile";
SET GLOBAL local_infile = 1;


-- Load Episode.tsv into Episode table

LOAD DATA LOCAL INFILE '/tmp/title.episode.tsv'
INTO TABLE episodes
COLUMNS TERMINATED BY '\t'
IGNORE 1 LINES
(episode_title_id, show_title_id, @season, @episode)
SET
  season_number  = NULLIF(@season, '\N'),
  episode_number = NULLIF(@episode, '\N');

-- Load Principals.tsv into Principals table
LOAD DATA LOCAL INFILE '/tmp/title.principals.tsv'
INTO TABLE crew
COLUMNS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    title_id,        -- tconst
    @ordering,       -- ordering (ignored)
    person_id,       -- nconst
    @category,
    @job,
    @show_characters
)
SET
    category  = NULLIF(@category, '\N'),
    job = NULLIF(@job, '\N'),
    show_characters = NULLIF(@show_characters, '\N');


-- Load Titles.tsv into Titles table
LOAD DATA LOCAL INFILE '/tmp/title.basics.tsv'
INTO TABLE titles
COLUMNS TERMINATED BY '\t'
IGNORE 1 LINES
(
    title_id,        
    @title_type,       
    @primary_title,       
    @original_title,
    @is_adult,
    @start_year,
    @end_year,
    @runtime_minutes,
    genres
)
SET
    title_type  = NULLIF(@title_type, '\N'),
    primary_title = NULLIF(@primary_title, '\N'),
    original_title = NULLIF(@original_title, '\N'),
    is_adult = CASE
        WHEN @is_adult = '1' THEN 1
        WHEN @is_adult = '0' THEN 0
        ELSE NULL
    END,
    start_year = NULLIF(@start_year, '\N'),
    end_year = NULLIF(@end_year, '\N'),
    runtime_minutes = NULLIF(@runtime_minutes, '\N');

-- Load Title_ratings.tsv into Title_ratings table
LOAD DATA LOCAL INFILE  '/tmp/title.ratings.tsv'
INTO TABLE ratings
COLUMNS TERMINATED BY '\t'
IGNORE 1 LINES
(title_id, @rating, @votes)
SET
    rating = NULLIF(@rating, '\N'),
    votes = NULLIF(@votes, '\N')
;


-- Load People.tsv into People table
LOAD DATA LOCAL INFILE '/tmp/name.basics.tsv'
INTO TABLE people
COLUMNS TERMINATED BY '\t'
IGNORE 1 LINES
(person_id, @person_name, @born, @died, @primaryProfession, @knownForTitles)
SET
    person_name = NULLIF(@person_name, '\N'),
    born = NULLIF(@born, '\N'),
    died = NULLIF(@died, '\N')
;