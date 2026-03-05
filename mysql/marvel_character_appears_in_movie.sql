SELECT
c.title_id, JSON_UNQUOTE(JSON_EXTRACT(c.show_characters, '$[0]')) AS character_name
INTO OUTFILE 
    '/var/lib/mysql-files/marvel_character_appears_in_movie.csv' 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
ESCAPED BY '"'
LINES TERMINATED BY '\n'
FROM crew AS c
INNER JOIN marvel_movies m
    ON c.title_id = m.title_id
WHERE
     c.show_characters IS NOT NULL
    AND c.show_characters NOT LIKE '%Self%'
    AND LOWER(c.category) != 'self'
    AND c.category NOT LIKE 'archive_%'
GROUP BY c.title_id, character_name
ORDER BY c.title_id, character_name;