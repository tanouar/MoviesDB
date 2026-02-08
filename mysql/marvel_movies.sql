-- REGEX Explanation:
-- ^ means start of the string, and $ means end of the string. This ensures that we are matching the entire title and not just a part of it.
-- The REGEXP_REPLACE function is used to remove any non-alphanumeric characters from the primary_title, and convert it to lowercase.
-- ([^a-z]|$) : matches anything that is not a letter or a number, or the end of the string. This ensures that we are matching whole words and not substrings. For example, it will match "Iron Man" but not "Iron Mania".
SELECT
    title_id,
    primary_title,
    genres,
    start_year 
INTO OUTFILE '/var/lib/mysql-files/marvel_movies.csv' 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
FROM titles AS t
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
    AND t.start_year >= 2008
    AND t.start_year <= 2026
ORDER BY t.start_year;
