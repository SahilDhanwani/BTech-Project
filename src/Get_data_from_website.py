from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd

def get(url):
    print(f"Fetching data from: {url}")

    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no browser window)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(url)
        
        # Wait for the table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "w3-table"))
        )

        # ✅ Check if the table exists before proceeding
        tables = driver.find_elements(By.CLASS_NAME, "w3-table")
        if not tables:
            print("❌ No table found in Selenium!")
            driver.quit()
            return None
        
        print(f"✅ Found {len(tables)} tables in Selenium!")

        # Get page source after JavaScript has loaded
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        return soup

    except Exception as e:
        print("Error loading page:", e)
        driver.quit()
        return None


def candidates(year, total_pages=84):
    base_url = "https://www.myneta.info/LokSabha2024/index.php?action=summary&subAction=candidates_analyzed&sort=candidate"
    all_results = []

    for page in range(1, total_pages + 1):
        url = f"{base_url}&page={page}" if page > 1 else base_url
        soup = get(url)
        
        if not soup:
            print(f"❌ Failed to retrieve page {page}")
            continue
        
        tables = soup.find_all("table")
        if len(tables) < 5:
            print(f"❌ Table 5 missing on page {page}")
            continue

        table = tables[4]  # Table 5 is at index 4
        print(f"✅ Scraping Table 5 from Page {page}!")

        rows = table.find_all("tr")
        for row in rows[1:]:  # Skip header row
            td = row.find_all("td")
            if len(td) < 8:
                continue

            candidate_link = td[1].find("a")
            candidate_name = candidate_link.text.strip() if candidate_link else "Unknown"
            
            candidate_id = None
            if candidate_link and "candidate_id=" in candidate_link["href"]:
                candidate_id = candidate_link["href"].split("candidate_id=")[-1].split("&")[0]
                candidate_id = int(candidate_id) if candidate_id.isdigit() else None

            all_results.append({
                "Year": year,
                "Sno": td[0].text.strip() if td[0].text else None,
                "ID": candidate_id,
                "Candidate": candidate_name,
                "Constituency": td[2].text.strip() if td[2].text else None,
                "Party": td[3].text.strip() if td[3].text else None,
                "Criminal Cases": int(td[4].get_text(strip=True)) if td[4].get_text(strip=True).isdigit() else 0,
                "Education": td[5].text.strip() if td[5].text else None,
                "Total Assets": td[6].get_text(strip=True) if td[6].get_text(strip=True) else None,
                "Total Liabilities": td[7].get_text(strip=True) if td[7].get_text(strip=True) else None,
            })
        
        print(f"✅ Page {page} scraped! Total records so far: {len(all_results)}")
    
    return pd.DataFrame(all_results)

# Run for 2024 elections
ls2024 = candidates(2024, total_pages=84)
print(ls2024.head())  # Display first 5 rows

# Save to CSV
ls2024.to_csv("LokSabha_2024_Candidates.csv", index=False)
print("✅ Data saved to LokSabha_2024_Candidates.csv")
