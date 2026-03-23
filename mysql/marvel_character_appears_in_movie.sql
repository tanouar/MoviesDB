SELECT DISTINCT
    c.title_id,
    jt.character_name
INTO OUTFILE
    '/var/lib/mysql-files/marvel_character_appears_in_movie.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\n'
FROM crew AS c
INNER JOIN marvel_movies m
    ON c.title_id = m.title_id
CROSS JOIN JSON_TABLE(
    c.show_characters,
    '$[*]' COLUMNS (character_name VARCHAR(255) PATH '$')
) AS jt
WHERE
    c.show_characters IS NOT NULL
    AND c.show_characters NOT LIKE '%Self%'
    AND LOWER(c.category) != 'self'
    AND c.category NOT LIKE 'archive_%'
    AND jt.character_name NOT LIKE '%Self%'
ORDER BY c.title_id, jt.character_name;