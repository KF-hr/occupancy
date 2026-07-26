import requests
import pandas as pd
from datetime import datetime
import copy
import json

# API
url = "https://wabi-north-europe-f-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true"

headers = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://app.powerbi.com",
    "Referer": "https://app.powerbi.com/",
    "User-Agent": "Mozilla/5.0",
    "X-PowerBI-ResourceKey": "d80ef85c-e1d2-4c36-8b1d-786e76b9b736"
}

def update_stations(payload, stations):

    def escape_station(s):
        return s.replace("'", "''")

    station_values = [
        [{"Literal": {"Value": f"'{escape_station(s)}'"}}]
        for s in stations
    ]

    sub_where = payload["queries"][0]["Query"]["Commands"][0]["SemanticQueryDataShapeCommand"]["Query"]["From"][4]["Expression"]["Subquery"]["Query"]["Where"]
    for cond in sub_where:
        if "In" in cond["Condition"]:
            expr = cond["Condition"]["In"]["Expressions"][0]["Column"]
            if expr["Expression"]["SourceRef"]["Source"] == "s1":
                cond["Condition"]["In"]["Values"] = station_values

    main_where = payload["queries"][0]["Query"]["Commands"][0]["SemanticQueryDataShapeCommand"]["Query"]["Where"]

    for cond in main_where:
        if "In" in cond["Condition"] and "Values" in cond["Condition"]["In"]:
            expr = cond["Condition"]["In"]["Expressions"][0]["Column"]
            if expr["Expression"]["SourceRef"]["Source"] == "s":
                cond["Condition"]["In"]["Values"] = station_values

    return payload


def update_date(payload, start_date, end_date):

    sub_where = payload["queries"][0]["Query"]["Commands"][0]["SemanticQueryDataShapeCommand"]["Query"]["From"][4]["Expression"]["Subquery"]["Query"]["Where"]

    for cond in sub_where:
        if "And" in cond["Condition"]:
            cond["Condition"]["And"]["Left"]["Comparison"]["Right"]["Literal"]["Value"] = f"datetime'{start_date}T00:00:00'"
            cond["Condition"]["And"]["Right"]["Comparison"]["Right"]["Literal"]["Value"] = f"datetime'{end_date}T00:00:00'"

    main_where = payload["queries"][0]["Query"]["Commands"][0]["SemanticQueryDataShapeCommand"]["Query"]["Where"]

    for cond in main_where:
        if "And" in cond["Condition"]:
            cond["Condition"]["And"]["Left"]["Comparison"]["Right"]["Literal"]["Value"] = f"datetime'{start_date}T00:00:00'"
            cond["Condition"]["And"]["Right"]["Comparison"]["Right"]["Literal"]["Value"] = f"datetime'{end_date}T00:00:00'"

    return payload


def parse_powerbi(result):

    ds = result["results"][0]["result"]["data"]["dsr"]["DS"][0]

    stations = [x["G4"] for x in ds["SH"][0]["DM2"]]
    rows = ds["PH"][0]["DM1"]

    data = []

    for r in rows:

        C = r["C"]
        
        timestamp = C[-1]

        if not isinstance(timestamp, (int, float)):
            continue

        date = pd.to_datetime(timestamp, unit="ms")
        values = [x.get("M2", None) for x in r["X"]]
        if len(values) < len(stations):
            values += [None] * (len(stations) - len(values))
        data.append([date] + values)

    df = pd.DataFrame(data, columns=["Date"] + stations)
    df = (
        df
        .sort_values("Date")
        .drop_duplicates("Date")
        .reset_index(drop=True)
    )

    return df

if __name__ == "__main__":

    with open("payload_template.json", "r", encoding="utf-8") as f:
        base_payload = json.load(f)

    all_stations = [
        "Paddington","Edgware Road","Marylebone","Baker Street","Great Portland Street",
        "Warren Street","Euston","Kings Cross St. Pancras","Angel","Old Street","Liverpool Street",
        "Bethnal Green","Whitechapel","Aldgate East","Aldgate","Tower Hill","Tower Gateway",
        "Monument","Bank","Moorgate","St Pauls","Farringdon","Barbican","Chancery Lane","Russell Square", 
        "Holborn","Euston Square","Goodge Street","Tottenham Court Road","Oxford Circus","Regents Park", 
        "Notting Hill Gate","Queensway","Lancaster Gate","Marble Arch","Bond Street","Bayswater",
        "Gloucester Road","South Kensington","Knightsbridge","Hyde Park Corner","Green Park","Piccadilly Circus",
        "Leicester Square","Covent Garden","High Street Kensington","Sloane Square","Victoria","St James's Park",
        "Westminster","Embankment","Temple","Blackfriars","Mansion House","Cannon Street","Charing Cross",
        "Pimlico","Vauxhall","Waterloo","Southwark","London Bridge","Canary Wharf","Stratford"
    ]

    start_date = "2025-01-01"
    end_date = "2026-01-01"

    final_df = None

    for i in range(0, len(all_stations), 10):

        batch = all_stations[i:i+10]
        print(f"Fetching stations: {batch}")

        payload = copy.deepcopy(base_payload)

        payload = update_date(payload, start_date, end_date)
        payload = update_stations(payload, batch)

        response = requests.post(url, json=payload, headers=headers)
        result = response.json()

        df = parse_powerbi(result)

        if final_df is None:
            final_df = df

        else:
            final_df = pd.merge(
                final_df,
                df,
                on="Date",
                how="outer"
            )

    final_df = (
        final_df
        .sort_values("Date")
        .drop_duplicates("Date")
        .reset_index(drop=True)
    )

    start_date_str = pd.to_datetime(start_date).year % 100
    end_date_str = pd.to_datetime(end_date).year % 100
    filename = f"data/original/{start_date_str:02d}{end_date_str:02d}_original.csv"

    final_df.to_csv(filename, index=False)

    print(f"Saved to {filename}")