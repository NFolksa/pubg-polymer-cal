from flask import Flask, render_template, request, jsonify
import requests
import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
from collections import defaultdict
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

app = Flask(__name__)

# Configuring logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# Steam Community Market URL
url = "https://steamcommunity.com/market/itemordershistogram"

# Item mapping: item_nameid to (name, fragment count)
item_nameid_name_mapping = {
    175977920: ('Desert Digital - Kar98k', 28),
    175977929: ('Desert Digital - M416', 40),
    175982684: ('Desert Digital - Micro UZI', 16),
    175977918: ('Desert Digital - Mini14', 28),
    175982682: ('Desert Digital - P18C', 16),
    175982688: ('Desert Digital - P92', 28),
    175977922: ('Desert Digital - R45', 16),
    175982689: ('Desert Digital - Sawed-Off', 16),
    175982681: ('Desert Digital - Win94', 16),
    175977923: ('Gold Plate  - Sawed-Off', 28),
    175982691: ('Gold Plate - AKM', 200),
    175982686: ('Gold Plate - AWM', 40),
    175982685: ('Gold Plate - Groza', 40),
    175977924: ('Gold Plate - S12K', 200),
    175977934: ('Gold Plate - SKS', 40),
    176099214: ('Gold Plate - UMP45', 28),
    176099206: ('Gold Plate - Vector', 28),
    175977921: ('Gold Plate - Win94', 16),
    176099204: ('Gunsmith Cobalt - PP-19 Bizon', 8),
    176099202: ('Gunsmith Cobalt - QBU', 8),
    176099209: ('Gunsmith Crimson - Win94', 8),
    176099208: ('Gunsmith Cobalt - P1911', 8),
    176099201: ('Gunsmith Crimson - AKM', 8),
    176099213: ('Gunsmith Crimson - S12K', 8),
    175976369: ('Jungle Digital - AWM', 40),
    176099216: ('Jungle Digital - M16A4', 16),
    175976363: ('Jungle Digital - P18C', 16),
    175976368: ('Jungle Digital - SKS', 28),
    176099211: ('Lucky Knight - M24', 40),
    176099215: ('Lucky Knight - SKS', 40),
    175976359: ('Rugged (Beige) - Crossbow', 8),
    175976364: ('Rugged (Beige) - Kar98k', 8),
    175976357: ('Rugged (Beige) - M16A4', 8),
    175976358: ('Rugged (Beige) - S12K', 8),
    175976355: ('Rugged (Beige) - S686', 8),
    175976356: ('Rugged (Beige) - SKS', 8),
    175977919: ('Rugged (Orange) - AKM', 16),
    175977915: ('Rugged (Orange) - Kar98k', 16),
    175977928: ('Rugged (Orange) - SCAR-L', 16),
    176045030: ('Rugged (Orange) - UMP45', 16),
    176099203: ('Silver Plate - AUG', 16),
    175976361: ('Silver Plate - DP-28', 16),
    175976354: ('Silver Plate - R1895', 8),
    175982690: ('Silver Plate - S12K', 40),
    175976360: ('Silver Plate - S1897', 16),
    175976367: ('Silver Plate - SCAR-L', 40),
    175982687: ('Silver Plate - Tommy Gun', 28),
    176045028: ('Silver Plate - UMP45', 28),
    175976366: ('Silver Plate - Vector', 28),
    176099210: ('Silver Plate - VSS', 16),
    176099205: ('Tick Tock - M416', 200),
    176099217: ('Tick Tock - QBZ', 40),
    176100169: ('Toxic - S1897', 28),
    175977916: ('Trifecta - Micro UZI', 28),
    175977933: ('Trifecta - P92', 16),
    175977926: ('Trifecta - SCAR-L', 40),
    175976370: ('Turquoise Delight - Kar98k', 200),
    175976371: ('Turquoise Delight - M16A4', 200),
    175976362: ('Turquoise Delight - P1911', 28),
    175976374: ('Turquoise Delight - Tommy Gun', 40)

}

# User-Agent generator
ua = UserAgent()

# Dictionary to store results
results = {}


def fetch_data(item_nameid):
    """Fetch data from the Steam Community Market for a given item_nameid."""
    params = {
        'country': 'CN',
        'language': 'schinese',
        'currency': 23,
        'item_nameid': item_nameid,
        'two_factor': 0,
    }
    try:
        response = session.get(url, headers={'User-Agent': ua.random}, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        results[item_nameid] = data.get('sell_order_graph', [])
    except requests.HTTPError as http_err:
        logging.error(f"HTTP error occurred for item_nameid {item_nameid}: {http_err}")
    except requests.RequestException as req_err:
        logging.error(f"Request failed for item_nameid {item_nameid}: {req_err}")
    except Exception as e:
        logging.error(f"Unexpected error fetching data for item_nameid {item_nameid}: {e}")


def calculate_purchase(number):
    """Calculate the optimal purchase details for a given number of fragments."""
    all_data = []
    for item_nameid, sell_order_graph in results.items():
        item_name, fragment_count = item_nameid_name_mapping[item_nameid]
        for price, quantity, _ in sell_order_graph:
            if price > 10:
                break
            all_data.append({
                'name': item_name,
                'decompose_count': fragment_count,
                'sale_price': price,
                'max_count': quantity,
                'surplus_count': quantity,
            })

    total_decompose_count = 0
    total_amount = 0.0
    need_buy_count = number
    purchase_details = defaultdict(lambda: {"buy_count": 0, "decompose_count": 0, "total_price": 0.0})

    while need_buy_count > 0:
        min_price_item = sorted(
            (item for item in all_data if item['surplus_count'] > 0),
            key=lambda x: x['sale_price'] / x['decompose_count']
        )

        if min_price_item:
            min_item = min_price_item[0]
            max_can_buy_count = min_item['decompose_count'] * min_item['surplus_count']

            if max_can_buy_count <= need_buy_count:
                buy_count = min_item['surplus_count']
            else:
                buy_count = math.ceil(need_buy_count / min_item['decompose_count'])

            decompose_count = min_item['decompose_count'] * buy_count
            need_buy_count -= decompose_count
            cur_amount = min_item['sale_price'] * buy_count
            total_amount += cur_amount
            total_decompose_count += decompose_count

            purchase_details[min_item['name']]['buy_count'] += buy_count
            purchase_details[min_item['name']]['decompose_count'] += decompose_count
            purchase_details[min_item['name']]['total_price'] += cur_amount

            min_item['surplus_count'] -= buy_count
        else:
            break

    sorted_purchase_details = sorted(
        [{"name": k, **v} for k, v in purchase_details.items()],
        key=lambda x: x['name']
    )

    return sorted_purchase_details, total_amount, total_decompose_count

@app.route("/calculate", methods=["POST"])
def calculate():
    """Handle the /calculate POST request to calculate purchase details."""
    number = int(request.json["number"])
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_data, item_nameid) for item_nameid in item_nameid_name_mapping.keys()]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Exception occurred: {e}")

    purchase_details, total_amount, total_decompose_count = calculate_purchase(number)
    return jsonify({
        "purchase_details": purchase_details,
        "total_amount": total_amount,
        "total_decompose_count": total_decompose_count
    })

@app.route("/", methods=["GET"])
def index():
    """Render the index page."""
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
