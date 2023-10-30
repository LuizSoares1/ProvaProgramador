import datetime
import json
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import concurrent.futures
from dataclasses import dataclass
import argparse

import tqdm


@dataclass
class Item:
    sport_league: str = (
        ""
    )
    event_date_utc: str = ""
    team1: str = ""
    team2: str = ""
    pitcher: str = ""
    period: str = ""
    line_type: str = (
        ""
    )
    price: str = ""
    side: str = ""
    team: str = (
        ""
    )
    spread: float = 0.0
    
    
def clean_items(items):
    new_items = items

    na_indices = []

    
    if "DRAW" in new_items:
        draw_item = items[items.index("DRAW")]
        items.pop(items.index("DRAW") + 1)
        items.remove(draw_item)
        
    for index, item in enumerate(new_items):
        if "N/A" in item:
            na_indices.append(index)

    for index in reversed(na_indices):
        new_items.insert(index + 1, "N/A")


    last_tem = new_items[-1]
    new_items.remove(last_tem)

    return new_items



def parse_price(price):
    if price == "N/A" or price == "":
        return None
    if " " in price:
        return float(price.split(" ")[1])
    if "." in price:
        return float(price)
    if price.startswith("+"):
        return int(price[1:])
    if price.startswith("-"):
        return -int(price[1:])
    if not price.isnumeric():
        return None
    return int(price)


def create_m1_and_m2(items, period, iso_8601_date_time, args):
    price = parse_price(str(items[2]))

    if price:
        ml_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="moneyline",
            price=items[2],
            side=items[1] if price > 0 else items[7],
            team=items[1] if price > 0 else items[7],
            spread=0,
        )
    elif not args.handle_na:
        ml_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="moneyline",
            price=items[2],
            side="N/A",
            team="N/A",
            spread=0,
        )

    price = parse_price(str(items[8]))

    if price:
        ml_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="moneyline",
            price=items[8],
            side=items[1] if price > 0 else items[7],
            team=items[1] if price > 0 else items[7],
            spread=0,
        )
    elif not args.handle_na:
        ml_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="moneyline",
            price=items[8],
            side="N/A",
            team="N/A",
            spread=0,
        )
    return ml_1, ml_2


def create_spread1_and_spread2(items, period, iso_8601_date_time, args):
    price = parse_price(str(items[3]))

    if price:
        spread_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="spread",
            price=items[4].replace("(", "").replace(")", ""),
            side=items[1] if price > 0 else items[7],
            team=items[1] if price > 0 else items[7],
            spread=price,
        )

        price = parse_price(str(items[9]))

        spread_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="spread",
            price=items[10].replace("(", "").replace(")", ""),
            side=items[1] if price > 0 else items[7],
            team=items[1] if price > 0 else items[7],
            spread=price,
        )

    elif not args.handle_na:
        price = "N/A"
        spread_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="spread",
            price=price,
            side=price,
            team=price,
            spread=price,
        )
        spread_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="spread",
            price=price,
            side=price,
            team=price,
            spread=price,
        )
    return spread_1, spread_2


def create_over_under1_and_over_under2(items, period, iso_8601_date_time, args):
    string_price = items[5]
    if " " in string_price:
        price = parse_price(str(string_price.split(" ")[1]))
    else:
        price = parse_price(str(string_price))
    if price:
        over_under_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="over/under",
            price=items[6].replace("(", "").replace(")", ""),
            side="over" if "O" in items[5] else "under",
            team="total",
            spread=price,
        )

        price = parse_price(str(items[11].split(" ")[1]))

        over_under_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="over/under",
            price=items[12].replace("(", "").replace(")", ""),
            side="over" if "O" in items[11] else "under",
            team="total",
            spread=price,
        )

    elif not args.handle_na:
        price = "N/A"

        over_under_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="over/under",
            price=price,
            side=price,
            team="total",
            spread=price,
        )

        over_under_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="over/under",
            price=price,
            side=price,
            team="total",
            spread=price,
        )
    return over_under_1, over_under_2


def process_row(row, args):
    items = row.text.split("\n")

    if len(items) <= 5:
        return

    bets = []

    items = clean_items(items)

    string_period = items[0].split(" ")

    period = f"{string_period[0]} {string_period[1]}"
    
    date_time_str = items[-1]
    
    input_format_with_date = "%I:%M %p ET (%m/%d/%Y)"
    input_format_without_date = "%I:%M %p ET"

    today_date = datetime.date.today()

    try:
        date_time = datetime.datetime.strptime(date_time_str, input_format_with_date)
    except ValueError:
        try:
            date_time = datetime.datetime.strptime(date_time_str, input_format_without_date)
            date_time = datetime.datetime.combine(today_date, date_time.time())
        except ValueError:
            print(f"Error processing date time: {date_time_str} is in an unsupported format")

    iso_8601_date_time = date_time.isoformat()

    try:
        ml_1, ml_2 = create_m1_and_m2(items, period, iso_8601_date_time, args)
        

        bets.append(ml_1)
        bets.append(ml_2)

    except Exception:
        pass

    try:
        spread_1, spread_2 = create_spread1_and_spread2(items, period, iso_8601_date_time, args)
        

        bets.append(spread_1)
        bets.append(spread_2)

    except Exception:
        pass

    try:
        over_under_1, over_under_2 = create_over_under1_and_over_under2(items, period, iso_8601_date_time, args)
        

        bets.append(over_under_1)
        bets.append(over_under_2)

    except Exception:
        pass

    bets_for_game = []
    for game in bets:
        game_data = {
            "sport league": game.sport_league,
            "event date (UTC)": game.event_date_utc,
            "team 1": game.team1,
            "team 2": game.team2,
            "pitcher": game.pitcher,
            "period": game.period,
            "line type": game.line_type,
            "price": game.price,
            "side": game.side,
            "team": game.team,
            "spread": game.spread,
        }
        bets_for_game.append(game_data)
    games_with_names.append(bets_for_game)



user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/99.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/99.0.1158.58",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/99.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Edge/99.0.1158.58",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Safari/605.1.15",
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape and process data from Veri Bet")
    parser.add_argument("-nna", "--handle_na", action="store_true", help="Do not Add 'N/A' for missing values")
    parser.add_argument("--noheadless", action="store_true", help="Disable headless mode for Chrome WebDriver")
    args = parser.parse_args()

    if not args.handle_na:
        print("The -nna flag was not provided, so 'N/A' values will be added for missing values.")
    else:
        print("The -nna flag was provided, 'N/A' values will not be added.")

    if args.noheadless:
        print("Headless mode is disabled.")
    else:
        print("Headless mode is enabled.")
    
    selected_user_agent = random.choice(user_agents)

    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={selected_user_agent}")
    
    if not args.noheadless:
        options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get("https://veri.bet/odds-picks?filter=upcoming")

    wait = WebDriverWait(driver, 30)

    table = wait.until(EC.presence_of_element_located((By.ID, "odds-picks")))

    table_data = []

    tbody = table.find_element(By.TAG_NAME, "tbody")


    rows = table.find_elements(By.CLASS_NAME, "col")

    games_with_names = []

    max_workers_percentage = 0.9
    max_workers = int(max_workers_percentage * os.cpu_count())
    

    print(f"Found {len(rows)} games. Starting parsing them using {max_workers} workers (cpu cores).")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers * 2) as executor:
        with tqdm.tqdm(total=len(rows), dynamic_ncols=True, position=0, file=sys.stdout) as progress_bar:
            def process_row_and_update_progress(row):
                process_row(row, args)
                progress_bar.update(1)

            futures = [executor.submit(process_row_and_update_progress, row) for row in rows]

            concurrent.futures.wait(futures)

    for game_data in games_with_names:
        print(json.dumps(game_data, indent=4))

    with open("parse_veri_bet_output.json", "w") as json_file:
        json.dump(games_with_names, json_file, indent=4)

    driver.quit()