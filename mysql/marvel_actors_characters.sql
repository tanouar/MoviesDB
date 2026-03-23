SELECT DISTINCT
    p.person_id,
    jt.character_name
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
ORDER BY p.person_id, jt.character_name;