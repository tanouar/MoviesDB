CREATE TABLE marvel_movies AS
SELECT
    title_id,
    primary_title,
    genres,
    start_year,
    runtime_minutes
FROM titles AS t
INNER JOIN marvel_films AS m 
    ON LOWER(t.primary_title) = LOWER(m.film)
    AND t.start_year = m.release_year
WHERE
    t.title_type IN ('movie', 'tv_series')
    AND t.start_year IS NOT NULL  
    AND genres IS NOT NULL
    AND runtime_minutes IS NOT NULL
ORDER BY t.start_year;