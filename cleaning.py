import os
import pandas as pd

def get_uk_holidays():
    dates = [
        # ===== 2021 =====
        "2021-01-01",
        "2021-04-02", "2021-04-05",
        "2021-05-03", "2021-05-31", "2021-08-30",
        "2021-12-27", "2021-12-28",

        # ===== 2022 =====
        "2022-01-03",
        "2022-04-15", "2022-04-18",
        "2022-05-02",
        "2022-06-02", "2022-06-03",
        "2022-08-29",
        "2022-09-19",
        "2022-12-26", "2022-12-27",

        # ===== 2023 =====
        "2023-01-02",
        "2023-04-07", "2023-04-10",
        "2023-05-01", "2023-05-08",
        "2023-05-29", "2023-08-28",
        "2023-12-25", "2023-12-26",

        # ===== 2024 =====
        "2024-01-01",
        "2024-03-29", "2024-04-01",
        "2024-05-06", "2024-05-27",
        "2024-08-26",
        "2024-12-25", "2024-12-26",

        # ===== 2025 =====
        "2025-01-01",
        "2025-04-18", "2025-04-21",
        "2025-05-05", "2025-05-26",
        "2025-08-25",
        "2025-12-25", "2025-12-26",

    ]

    return pd.to_datetime(dates)


def clean_tfl_data(df):

    df["Date"] = pd.to_datetime(df["Date"])

    df = df[df["Date"].dt.weekday < 5]

    # =========================
    # Remove Bank Holidays
    # =========================
    holiday_list = get_uk_holidays()
    df = df[~df["Date"].isin(holiday_list)]

    # =========================
    # Remove Christmas period
    # =========================
    def is_christmas(date):
        return (
            (date.month == 12 and date.day >= 24) or
            (date.month == 1 and date.day <= 1)
        )

    df = df[~df["Date"].apply(is_christmas)]

    # =========================
    # Remove Easter Break
    # =========================
    # def is_easter(date):
    #     return (
    #         (date.month == 3 and date.day >= 25) or
    #         (date.month == 4 and date.day <= 10)
    #     )

    # df = df[~df["Date"].apply(is_easter)]

    df = df.sort_values("Date").reset_index(drop=True)
    return df


if __name__ == "__main__":

    input_dir = "data/original"
    output_dir = "data/clean"

    os.makedirs(output_dir, exist_ok=True)

    files = [f for f in os.listdir(input_dir) if f.endswith("_original.csv")]
    
    all_dfs = []

    for file in files:

        print(f"\nProcessing {file}...")

        input_path = os.path.join(input_dir, file)

        df = pd.read_csv(input_path)
        original_rows = len(df)

        df_clean = clean_tfl_data(df)
        clean_rows = len(df_clean)
    
        all_dfs.append(df_clean)

        output_file = file.replace("_original", "_clean")
        output_path = os.path.join(output_dir, output_file)

        df_clean.to_csv(output_path, index=False)

        print(f"Saved: {output_file}")
        print(f"Rows: {original_rows} → {clean_rows}")

    # Concat all cleaned data
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df = final_df.sort_values("Date").reset_index(drop=True)
    final_output = os.path.join(output_dir, "total_data.csv")
    final_df.to_csv(final_output, index=False)

    print(f"\n Saved combined file → {final_output}")
    print(f"Total rows: {len(final_df)}")

    # Compute rolling average 
    df_rolling = final_df.copy()
    df_rolling["Date"] = pd.to_datetime(df_rolling["Date"])

    df_rolling = df_rolling.set_index("Date")
    df_rolling = df_rolling.rolling(window=30).mean()
    df_rolling = df_rolling.reset_index()

    rolling_output = os.path.join(output_dir, "total_data_rolling30.csv")
    df_rolling.to_csv(rolling_output, index=False)

    print(f"\nSaved rolling file → {rolling_output}")
    