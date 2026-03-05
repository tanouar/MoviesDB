SELECT
m.title_id, p.person_id
INTO OUTFILE 
    '/var/lib/mysql-files/marvel_person_directs_movie.csv' 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\n'
FROM crew c
INNER JOIN marvel_movies m
    ON c.title_id = m.title_id
INNER JOIN people p
    ON c.person_id = p.person_id
WHERE
    -- (
    --     LOWER(c.job) LIKE '%director%'
    --     OR LOWER(c.job) LIKE '%producer%'
    --     OR LOWER(c.category) LIKE '%director%'
    -- )
    -- AND 
    (
        LOWER(c.category) = 'director'
        -- OR LOWER(c.category) = 'self'
    )
    AND c.show_characters IS NULL
ORDER BY m.title_id;