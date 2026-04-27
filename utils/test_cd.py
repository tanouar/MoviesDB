import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://mcugraph.streamlit.app/"

opts = Options()
# Activer pour exécuter sans interface graphique
# opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-gpu")
opts.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=opts,
)

try:
    driver.get(URL)
    print(f"Titre : {driver.title}")
    # Maintenir la session WebSocket ouverte 15 secondes
    time.sleep(15)
    print("Session active — succès.")

finally:
    driver.quit()
