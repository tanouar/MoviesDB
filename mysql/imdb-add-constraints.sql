ALTER TABLE titles
ADD PRIMARY KEY (title_id);

ALTER TABLE episodes
ADD PRIMARY KEY (episode_title_id);

ALTER TABLE people
ADD PRIMARY KEY (person_id);


ALTER TABLE ratings
ADD PRIMARY KEY (title_id);

-- SET foreign_key_checks = 0;

-- ALTER TABLE episodes
-- ADD CONSTRAINT episode_show_title_id_fkey FOREIGN KEY (show_title_id) REFERENCES titles(title_id);

-- ALTER TABLE crew
-- ADD CONSTRAINT crew_person_id_fkey FOREIGN KEY (person_id) REFERENCES people(person_id);

-- ALTER TABLE crew
-- ADD CONSTRAINT crew_title_id_fkey FOREIGN KEY (title_id) REFERENCES titles(title_id);

-- ALTER TABLE ratings
-- ADD CONSTRAINT ratings_title_id_fkey FOREIGN KEY (title_id) REFERENCES titles(title_id);