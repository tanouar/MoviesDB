import pandas as pd
import requests
from io import StringIO
import re


def clean_wiki_title(title):
    if not isinstance(title, str):
        return title

    title = re.sub(r"\[.*?\]", "", title)      # remove citations like [1], [d]
    title = title.replace("\u2009", " ")       # replace thin space
    title = re.sub(r"\s+", " ", title)         # normalize whitespace
    title = title.strip()

    return title


def main():
    url = (
        "https://en.wikipedia.org/wiki/"
        "List_of_Marvel_Cinematic_Universe_films"
    )

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    tables = pd.read_html(StringIO(response.text))

    film_tables = [
        t for t in tables
        if any(str(c).strip().startswith("Film") for c in t.columns)
    ]

    # print(f"Number of tables found: {len(film_tables)}")

    # for i, t in enumerate(film_tables):
    #     print(i, t.shape, t.columns)

    clean_tables = []

    for t in film_tables:

        # remove citation markers like Film[41]
        t.columns = [
            re.sub(r"\[.*?\]", "", str(c)).strip()
            for c in t.columns
        ]

        clean_tables.append(t)

    # concatenate them
    marvel_df = (
        pd.concat(clean_tables, ignore_index=True)
        # .dropna(subset=["Film"])
    )
    marvel_df = marvel_df.rename(columns={
        "Film": "film",
        "U.S. release date": "release_date"
    })

    marvel_df["film"] = marvel_df["film"].apply(clean_wiki_title)
    marvel_df["release_date"] = marvel_df["release_date"].apply(
        clean_wiki_title)
    marvel_df["release_date"] = marvel_df["release_date"].replace(
        ["TBA", "—"], pd.NA
    )
    marvel_df["release_date"] = pd.to_datetime(
        marvel_df["release_date"],
        errors="coerce"
    )
    today = pd.Timestamp.today()

    released_films = marvel_df[
        (marvel_df["release_date"].notna()) &
        (marvel_df["release_date"] <= today)
    ]
    released_films = released_films.copy()
    released_films.loc[:, "release_year"] = (
        released_films["release_date"].dt.year.astype("Int64")
    )

    released_films.loc[:, ["film", "release_year"]].to_csv(
        "data/raw/marvel_films.csv",
        index=False
    )


if __name__ == "__main__":
    main()
