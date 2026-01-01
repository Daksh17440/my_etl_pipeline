import requests
import urllib.parse
from datetime import datetime
import json

session = requests.Session()

# UPDATE YOUR JSESSIONID HERE
cookies = {
    'JSESSIONID': '....YOUR_JSESSIONID_HERE....', 
}

headers_common = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8,hi;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://indiawris.gov.in',
    'Referer': 'https://indiawris.gov.in/dataSet/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-mobile': '?0',
}

session.cookies.update(cookies)
session.headers.update(headers_common)

def get_selection(options, prompt_text):
    print(f"\n--- {prompt_text} ---")
    for idx, (name, code) in enumerate(options):
        print(f"{idx + 1}. {name}")
    
    while True:
        try:
            choice = int(input(f"\nEnter number (1-{len(options)}): "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print("Invalid number. Try again.")
        except ValueError:
            print("Please enter a valid number.")

def get_date_input(prompt_text):
    while True:
        date_str = input(f"{prompt_text} (YYYY-MM-DD): ")
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            print("Invalid format. Please use YYYY-MM-DD (e.g., 2023-11-01)")

def main():
    print("Initializing India-WRIS Downloader...")

    # --- STEP 1: Get Datasets ---
    print("\nFetching Datasets...")
    url_datasets = 'https://indiawris.gov.in/DataSet/DataSetList'
    try:
        resp = session.post(url_datasets, json={'headers': {'normalizedNames': {}, 'lazyUpdate': None}})
        resp.raise_for_status()
        data = resp.json()
        
        dataset_options = []
        items = data.get('data', []) if isinstance(data, dict) else data

        for item in items:
            name = (item.get('datasetdescription') or item.get('dname') or item.get('dataSetName'))
            code = (item.get('datasetcode') or item.get('dcode') or item.get('dataSetCode'))
            
            if name and code:
                dataset_options.append((name, code))
        
        dataset_options.sort()
        
        if not dataset_options:
            print("No datasets found.")
            return

        selected_dname, selected_dcode = get_selection(dataset_options, "SELECT DATASET")
        print(f"Selected: {selected_dname} ({selected_dcode})")

    except Exception as e:
        print(f"Error fetching datasets: {e}")
        return

    print("\nFetching States...")
    url_states = 'https://indiawris.gov.in/masterState/StateList'
    try:
        resp = session.post(url_states, json={'datasetcode': selected_dcode})
        resp.raise_for_status()
        state_data = resp.json()
        
        state_options = []
        items = state_data.get('data', []) if isinstance(state_data, dict) else state_data

        for item in items:
            name = (item.get('state') or item.get('stateName') or item.get('statename'))
            code = (item.get('statecode') or item.get('stateCode'))
            
            if name and code:
                state_options.append((name, code))
        
        state_options.sort()
        
        if not state_options:
            print("No states found.")
            return

        selected_sname, selected_scode = get_selection(state_options, "SELECT STATE")
        print(f"Selected: {selected_sname}")

    except Exception as e:
        print(f"Error fetching states: {e}")
        return

    print(f"\nFetching Districts for {selected_sname}...")
    url_districts = 'https://indiawris.gov.in/masterDistrict/getDistrictbyState'
    try:
        resp = session.post(url_districts, json={'statecode': selected_scode, 'datasetcode': selected_dcode})
        resp.raise_for_status()
        dist_data = resp.json()
        
        dist_options = []
        items = dist_data.get('data', []) if isinstance(dist_data, dict) else dist_data

        for item in items:
            name = (item.get('districtName') or 
                    item.get('districtname') or 
                    item.get('district'))
            
            code = (item.get('districtCode') or 
                    item.get('districtcode') or 
                    item.get('districtId') or 
                    item.get('district_id')) 
            if name and code:
                dist_options.append((name, code))
        
        dist_options.sort()
        
        if not dist_options:
            print("No districts found. Response dump:", json.dumps(dist_data, indent=2))
            return

        selected_distname, selected_distcode = get_selection(dist_options, "SELECT DISTRICT")
        print(f"Selected: {selected_distname}")

    except Exception as e:
        print(f"Error fetching districts: {e}")
        return

    print("\n--- SELECT DATE RANGE ---")
    start_date = get_date_input("Enter Start Date")
    end_date = get_date_input("Enter End Date")

    print("\nDownloading Data...")
    
    encoded_dname = urllib.parse.quote(selected_dname)
    download_url = f'https://indiawris.gov.in/Dataset/{encoded_dname}'
    
    params = {
        'stateName': selected_sname,
        'districtName': selected_distname,
        'agencyName': 'CGWB',
        'startdate': start_date,
        'enddate': end_date,
        'download': 'true',
        'page': '0',
        'size': '100000',
    }
    
    dl_headers = headers_common.copy()
    dl_headers['accept'] = 'text/csv'
    
    try:
        resp = session.post(download_url, params=params, headers=dl_headers)
        
        if resp.status_code == 200:
            safe_dname = selected_dname.replace(" ", "_").replace("/", "-")
            safe_dist = selected_distname.replace(" ", "_")
            filename = f"{safe_dname}_{safe_dist}_{start_date}_{end_date}.csv"
            
            with open(filename, "wb") as f:
                f.write(resp.content)
            
            print(f"\n✅ SUCCESS! File saved as: {filename}")
        else:
            print(f"\n❌ Download Failed. Status Code: {resp.status_code}")
            print("Response:", resp.text[:300])
            
    except Exception as e:
        print(f"Error during download: {e}")

if __name__ == "__main__":
    main()