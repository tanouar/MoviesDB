-- Create index for non-primary key columns to improve query performance

-- Title_year Index --
CREATE INDEX idx_titles_type_year ON titles(title_type, start_year);

-- Episodes Index --
CREATE INDEX idx_episodes_show_title_id ON episodes(show_title_id);

-- Crew Index --
CREATE INDEX idx_crew_title ON crew(title_id);

CREATE INDEX idx_crew_person ON crew(person_id);
