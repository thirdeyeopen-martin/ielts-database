import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import time
from io import BytesIO

st.set_page_config(page_title="IELTS Test Centre Database", layout="wide")

st.markdown("""
    <style>
        .main-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #004080;
            text-align: center;
        }
        .info-text {
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>IELTS Global Test Centre Scraper</div>", unsafe_allow_html=True)

st.markdown("""
<div class='info-text'>
    Select one or more countries to begin scraping detailed test centre data, including UKVI availability, test types, fees, and locations.
    Once complete, you'll be able to download the full dataset as an Excel spreadsheet.
</div>
""", unsafe_allow_html=True)

COUNTRIES = {
    "Albania": "alb",
    "Algeria": "dza",
    "Argentina": "arg",
    "Australia": "aus",
    "Austria": "aut",
    "Bangladesh": "bgd",
    "Brazil": "bra",
    "Canada": "can",
    "China": "chn",
    "France": "fra",
    "Germany": "deu",
    "India": "ind",
    "Italy": "ita",
    "Japan": "jpn",
    "Malaysia": "mys",
    "Nigeria": "nga",
    "Pakistan": "pak",
    "Philippines": "phl",
    "Saudi Arabia": "sau",
    "South Africa": "zaf",
    "United Kingdom": "gbr",
    "United States": "usa",
}

with st.sidebar:
    st.header("Scraper Control Panel")
    selected_countries = st.multiselect("Select countries to scrape:", options=list(COUNTRIES.keys()), default=["Albania"])
    start_button = st.button("🚀 Start Scraping")

if start_button:
    all_centres = []
    progress_bar = st.progress(0)

    for i, country in enumerate(selected_countries):
        country_code = COUNTRIES[country]
        st.write(f"🔍 Scraping test centres for {country}...")
        search_url = f"https://ielts.org/test-centres?country={country_code}"
        res = requests.get(search_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        cards = soup.select('.test-centre-card')

        for card in cards:
            name = card.select_one(".test-centre-card__title").get_text(strip=True) if card.select_one(".test-centre-card__title") else ""
            address = card.select_one(".test-centre-card__address").get_text(strip=True) if card.select_one(".test-centre-card__address") else ""
            rel_url = card.get("href")
            full_url = f"https://ielts.org{rel_url}" if rel_url and rel_url.startswith("/test-centres") else rel_url
            ukvi = "UKVI Approved" in card.get_text()
            osr = "One Skill Retake" in card.get_text()

            # Visit the detail page for deeper info
            fees = {}
            test_types = []
            if full_url:
                try:
                    detail_res = requests.get(full_url)
                    detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
                    fee_blocks = detail_soup.select(".product")
                    for block in fee_blocks:
                        test_type = block.select_one(".product-title").get_text(strip=True) if block.select_one(".product-title") else "Unknown"
                        price = block.select_one(".product-price").get_text(strip=True) if block.select_one(".product-price") else "Unknown"
                        fees[test_type] = price
                        test_types.append(test_type)
                    time.sleep(1)  # be nice to the server
                except:
                    pass

            all_centres.append({
                "Country": country,
                "Centre Name": name,
                "City": address.split(",")[-1].strip() if "," in address else "",
                "Address": address,
                "UKVI Approved": ukvi,
                "One Skill Retake": osr,
                "Test Types": ", ".join(test_types),
                "Fees": fees,
                "Detail Page": full_url
            })

        progress_bar.progress((i + 1) / len(selected_countries))

    if all_centres:
        df = pd.DataFrame(all_centres)
        st.success(f"✅ Scraped {len(df)} test centres across {len(selected_countries)} countries.")
        st.dataframe(df)

        # Create Excel in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Test Centres')
            writer.save()
            processed_data = output.getvalue()

        st.download_button(
            label="📥 Download Full Excel File",
            data=processed_data,
            file_name="IELTS_Global_Test_Centres.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No data found.")
