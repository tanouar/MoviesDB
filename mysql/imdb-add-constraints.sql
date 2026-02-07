ALTER TABLE titles
ADD PRIMARY KEY (title_id);

ALTER TABLE episodes
ADD PRIMARY KEY (episode_title_id);

ALTER TABLE people
ADD PRIMARY KEY (person_id);


ALTER TABLE ratings
ADD PRIMARY KEY (title_id);

-- SET foreign_key_checks = 0;

-- ALTER TABLE Episodes
-- ADD CONSTRAINT Episode_show_title_id_fkey FOREIGN KEY (show_title_id) REFERENCES Titles(title_id);

-- ALTER TABLE Crew
-- ADD CONSTRAINT Crew_name_id_fkey FOREIGN KEY (person_id) REFERENCES People(person_id);

-- ALTER TABLE Crew
-- ADD CONSTRAINT Crew_title_id_fkey FOREIGN KEY (title_id) REFERENCES Titles(title_id);