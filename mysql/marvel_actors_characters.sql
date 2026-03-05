SELECT
p.person_id, JSON_UNQUOTE(JSON_EXTRACT(c.show_characters, '$[0]')) AS character_name
INTO OUTFILE 
    '/var/lib/mysql-files/marvel_person_plays_character.csv' 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\n'
FROM people p
INNER JOIN crew c 
    ON p.person_id = c.person_id
INNER JOIN marvel_movies m 
    ON c.title_id = m.title_id
WHERE
     c.show_characters IS NOT NULL
    AND c.show_characters NOT LIKE '%Self%'
    AND LOWER(c.category) != 'self'
    AND c.category NOT LIKE 'archive_%'
GROUP BY p.person_id, c.show_characters
ORDER BY p.person_id;