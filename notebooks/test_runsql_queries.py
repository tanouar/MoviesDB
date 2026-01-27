# %%
from sqlalchemy import create_engine 
from pathlib import Path

# %%
# test de requete SQL
# DB_PATH = Path("/app/data/db/newIMDB.db") if Path("/app").exists() else Path("data/db/newIMDB.db")
engineIMDB = create_engine("sqlite:////app/data/db/newIMDB.db")

# engineIMDB = create_engine(f"sqlite:///{DB_PATH.resolve()}")
# engineIMDB = create_engine('sqlite:///data/db/newIMDB.db')
connIMDB = engineIMDB.connect()

result = connIMDB.execute("SELECT title_id,rating,votes" 
                          " FROM ratings"  
                          " WHERE votes > 5000" 
                          " ORDER BY rating" 
                          " DESC, ratings.votes" 
                          " DESC LIMIT 5")
print(result.fetchall())

# %%
result2 = connIMDB.execute("SELECT primary_title, rating, votes" 
                          " FROM titles" 
                          " INNER JOIN ratings" 
                          " ON titles.title_id=ratings.title_id" 
                          " WHERE votes > 5000" 
                          " ORDER BY ratings.rating" 
                          " DESC, ratings.votes" 
                          " DESC LIMIT 10")
print(result2.fetchall())


