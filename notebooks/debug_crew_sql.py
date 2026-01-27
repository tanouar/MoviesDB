# %%
# importation des bibliothèques
import requests
import pandas as pd
import sqlite3, sqlalchemy
from tqdm.notebook import trange, tqdm
from sqlalchemy import Table, Column, Integer, String, ForeignKey, MetaData, create_engine, text, inspect, Float


# liste des urls pour chaque fichier à telecharger
urls = ['https://datasets.imdbws.com/name.basics.tsv.gz',
       'https://datasets.imdbws.com/title.basics.tsv.gz', 
       'https://datasets.imdbws.com/title.episode.tsv.gz', 
       'https://datasets.imdbws.com/title.principals.tsv.gz', 
       'https://datasets.imdbws.com/title.ratings.tsv.gz']

# # telechargement des fichiers
# for url in urls:

#     target_path = str(url[28:])
#     response = requests.get(url, stream=True)  
   
#     if response.status_code == 200:
#         with open(target_path, 'wb') as f:
#             f.write(response.raw.read())
            
#     for i in trange(1, desc='Statut'):
#         print('Fichier téléchargé :', target_path)

# %%
# création de la base de données crew.db
engine = create_engine('sqlite:///crew.db', echo=False)
meta = MetaData()

# %%
################################################## title.ratings.tsv.gz ##################################################

# # chargement des données
# df_title_ratings = pd.read_csv('title.ratings.tsv.gz', compression='gzip', header=0, sep='\t')

# # transformation des données du dataframe en liste de tuple
# values = df_title_ratings.to_records(index=False).tolist()

# # création de la table ratings
# ratings = Table(
#     'ratings', meta, 
#     Column('title_id', String(20), primary_key=True), 
#     Column('rating', Float), 
#     Column('votes', String(20)),
#     extend_existing=True)

# meta.create_all(engine)

# # insertions des valeurs dans la table ratings
# # on crée la connection
# with engine.connect() as connection:
#     # début de la transaction
#     with connection.begin() as transaction:
#         # on tente d'éxécuter une transaction
#         try:
#             # On indique le format d'un tuple de cette table
#             markers = ','.join('?' * len(values[0])) 
            
#             # On utilise le langage SQL en format texte où markers est le format d'un tuple
#             ins = 'INSERT OR REPLACE INTO {tablename} VALUES ({markers})'
            
#             # On précise ce format particulier grâce à la fonction membre format
#             ins = ins.format(tablename=ratings.name, markers=markers)
           
#             # Enfin on peut utiliser les tuples créés en éxécutant la commande SQL
#             connection.execute(ins, values)
#         # si la transaction échoue
#         except:
#             transaction.rollback()
#             raise
#         # si la transaction réussit
#         else:
#             transaction.commit()

# # drop des data ratings
# df_title_ratings = []
# values = []

# %%
################################################## title.principals.tsv.gz ##################################################

# chargement des données
df_title_principals = pd.read_csv('data/raw/title.principals.tsv.gz', compression='gzip', header=0, sep='\t')

# suppresion d'une colonne
df_title_principals.pop('ordering')

# transformation des données du dataframe en liste de tuple
values = df_title_principals.to_records(index=False).tolist()

# création de la table ratings
crew = Table(
    'crew', meta, 
    Column('title_id', String(20), primary_key=False), 
    Column('person_id', String(20)), 
    Column('category', String(20)), 
    Column('job', String(200)), 
    Column('characters', String(200)) )
meta.create_all(engine)

# insertions des valeurs dans la table ratings
# on crée la connection
with engine.connect() as connection:
    # début de la transaction
    with connection.begin() as transaction:
        # on tente d'éxécuter une transaction
        try:
            # On indique le format d'un tuple de cette table
            markers = ','.join('?' * len(values[0])) 
            
            # On utilise le langage SQL en format texte où markers est le format d'un tuple
            ins = 'INSERT OR REPLACE INTO {tablename} VALUES ({markers})'
            
            # On précise ce format particulier grâce à la fonction membre format
            ins = ins.format(tablename=crew.name, markers=markers)
           
            # Enfin on peut utiliser les tuples créés en éxécutant la commande SQL
            connection.execute(ins, values)
        # si la transaction échoue
        except:
            transaction.rollback()
            raise
        # si la transaction réussit
        else:
            transaction.commit()
            
# drop des data ratings
df_title_principals = []
values = []

# %%
################################################## title.episode.tsv.gz ##################################################

# # chargement des données
# df_title_episode = pd.read_csv('title.episode.tsv.gz', compression='gzip', header=0, sep='\t')

# # transformation des données du dataframe en liste de tuple
# values = df_title_episode.to_records(index=False).tolist()


# # création de la table ratings
# episodes = Table(
#     'episodes', meta, 
#     Column('episode_title_id', String(20), primary_key=False), 
#     Column('show_title_id', String(20)), 
#     Column('season_number', Integer), 
#     Column('episode_number', Integer))

# meta.create_all(engine)

# # insertions des valeurs dans la table ratings
# # on crée la connection
# with engine.connect() as connection:
#     # début de la transaction
#     with connection.begin() as transaction:
#         # on tente d'éxécuter une transaction
#         try:
#             # On indique le format d'un tuple de cette table
#             markers = ','.join('?' * len(values[0])) 
            
#             # On utilise le langage SQL en format texte où markers est le format d'un tuple
#             ins = 'INSERT OR REPLACE INTO {tablename} VALUES ({markers})'
            
#             # On précise ce format particulier grâce à la fonction membre format
#             ins = ins.format(tablename=episodes.name, markers=markers)
           
#             # Enfin on peut utiliser les tuples créés en éxécutant la commande SQL
#             connection.execute(ins, values)
#         # si la transaction échoue
#         except:
#             transaction.rollback()
#             raise
#         # si la transaction réussit
#         else:
#             transaction.commit()
            
# # drop des data ratings
# df_title_episode = []
# values = []

# %%
################################################## title.basics.tsv.gz ##################################################

# chargement des données
# df_title_basics = pd.read_csv('title.basics.tsv.gz', compression='gzip', header=0, sep='\t')

# # transformation des données du dataframe en liste de tuple
# values = df_title_basics.to_records(index=False).tolist()


# # création de la table ratings
# titles = Table(
#     'titles', meta, 
#     Column('title_id', String(20), primary_key=False), 
#     Column('type', String(20)), 
#     Column('primary_title', String(200)), 
#     Column('original_title', String(200)), 
#     Column('is_adult', Integer), 
#     Column('premiered', Integer), 
#     Column('ended', Integer), 
#     Column('runtime_minutes', Integer), 
#     Column('genres', String(200)))

# meta.create_all(engine)

# # insertions des valeurs dans la table ratings
# # on crée la connection
# with engine.connect() as connection:
#     # début de la transaction
#     with connection.begin() as transaction:
#         # on tente d'éxécuter une transaction
#         try:
#             # On indique le format d'un tuple de cette table
#             markers = ','.join('?' * len(values[0])) 
            
#             # On utilise le langage SQL en format texte où markers est le format d'un tuple
#             ins = 'INSERT OR REPLACE INTO {tablename} VALUES ({markers})'
            
#             # On précise ce format particulier grâce à la fonction membre format
#             ins = ins.format(tablename=titles.name, markers=markers)
           
#             # Enfin on peut utiliser les tuples créés en éxécutant la commande SQL
#             connection.execute(ins, values)
#         # si la transaction échoue
#         except:
#             transaction.rollback()
#             raise
#         # si la transaction réussit
#         else:
#             transaction.commit()
            
# # drop des data ratings
# df_title_basics = []
# values = []

# %%
################################################## name.basics.tsv.gz ##################################################

# chargement des données
# df_name_basics = pd.read_csv('name.basics.tsv.gz', compression='gzip', header=0, sep='\t')

# # suppresion d'une colonne
# df_name_basics.pop('primaryProfession')
# df_name_basics.pop('knownForTitles')

# # transformation des données du dataframe en liste de tuple
# values = df_name_basics.to_records(index=False).tolist()


# # création de la table ratings
# people = Table(
#     'people', meta, 
#     Column('person_id', String(20), primary_key=False), 
#     Column('name', String(200)), 
#     Column('born', String(20)), 
#     Column('died', String(20)))

# meta.create_all(engine)

# # insertions des valeurs dans la table ratings
# # on crée la connection
# with engine.connect() as connection:
#     # début de la transaction
#     with connection.begin() as transaction:
#         # on tente d'éxécuter une transaction
#         try:
#             # On indique le format d'un tuple de cette table
#             markers = ','.join('?' * len(values[0])) 
            
#             # On utilise le langage SQL en format texte où markers est le format d'un tuple
#             ins = 'INSERT OR REPLACE INTO {tablename} VALUES ({markers})'
            
#             # On précise ce format particulier grâce à la fonction membre format
#             ins = ins.format(tablename=people.name, markers=markers)
           
#             # Enfin on peut utiliser les tuples créés en éxécutant la commande SQL
#             connection.execute(ins, values)
#         # si la transaction échoue
#         except:
#             transaction.rollback()
#             raise
#         # si la transaction réussit
#         else:
#             transaction.commit()
            
# # drop des data ratings
# df_name_basics = []
# values = []

# # %%
# # affichage du noms des tables dans la base de données newIMDB.db
# inspector = inspect(engine)
# inspector.get_table_names()

# # %%
# # affichage des noms de variables pour toutes les tables de la base newIMDB.db
# for table_name in inspector.get_table_names():
#     for column in inspector.get_columns(table_name):
#         print("Column: %s" % column['name'])

# # %%
# # test de requete SQL

# engineIMDB = create_engine('sqlite:///newIMDB.db')
# connIMDB = engineIMDB.connect()

# result = connIMDB.execute("SELECT primary_title, rating, votes" 
#                           " FROM titles" 
#                           " INNER JOIN ratings" 
#                           " ON titles.title_id=ratings.title_id" 
#                           " WHERE votes > 5000" 
#                           " ORDER BY ratings.rating" 
#                           " DESC, ratings.votes" 
#                           " DESC LIMIT 10")
# result.fetchall()


engineIMDB = create_engine('sqlite:///crew.db')
connIMDB = engineIMDB.connect()

result = connIMDB.execute("SELECT title_id,characters" 
                          " FROM crew" 
                          " WHERE category='actor'" 
                          " LIMIT 10")
result.fetchall()