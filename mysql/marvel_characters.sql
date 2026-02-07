WITH
    marvel_titles AS (
        SELECT title_id
        FROM Titles AS t
        WHERE
            REGEXP_REPLACE(
                LOWER(primary_title),
                '[^a-z0-9 ]',
                ''
            ) REGEXP '^(iron man|captain america|thor|the avengers|avengers|guardians of the galaxy|antman|hulk|black panther|doctor strange|captain marvel|spiderman|black widow|shangchi|wandavision|loki|hawkeye|moon knight|ms marvel|shehulk|eternals|deadpool|the marvels)([^a-z]|$)'
            AND REGEXP_REPLACE(
                LOWER(primary_title),
                '[^a-z0-9 ]',
                ''
            ) NOT REGEXP '(lego|reassembled|swat|business|cut|raimi|fan|bus|premiere)'
            -- LOWER(primary_title) REGEXP '^(iron man|captain america|thor:|the avengers|avengers:|guardians of the galaxy|ant-man|hulk|black panther|black panther:|doctor strange|captain marvel|spider-man|black widow|shang-chi|wandavision|loki|hawkeye|moon knight|ms\. marvel|she-hulk|thor: ragnarok|eternals|deadpool|the marvels)([^a-z]|$)'
            AND t.title_type IN ('movie', 'tv_series')
            AND (
                t.genres LIKE '%Action%'
                OR t.genres LIKE '%Adventure%'
                OR t.genres LIKE '%Comedy%'
                OR t.genres LIKE '%Drama%'
                OR t.genres LIKE '%Sci-Fi%'
                OR t.genres LIKE '%Fantasy%'
            )
            AND t.genres NOT LIKE '%Animation%'
            AND t.genres NOT LIKE '%Crime%'
            AND t.start_year IS NOT NULL
            AND t.start_year >= 2008 AND t.start_year <= 2026
    )
SELECT DISTINCT
    c.show_characters AS character_name
FROM Titles AS t
    INNER JOIN Crew AS c
    ON t.title_id = c.title_id
WHERE
    t.title_id IN (
        SELECT title_id
        FROM marvel_titles
    )
    AND c.show_characters IS NOT NULL
    AND c.show_characters NOT LIKE '%Self%'
    AND LOWER(c.category) != 'self'
    AND c.category NOT LIKE 'archive_%'
ORDER BY c.show_characters;
