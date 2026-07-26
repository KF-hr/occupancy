import pandas as pd
from sklearn.linear_model import LinearRegression


# -------------------------
# 1. Occupancy（已知数据）
# -------------------------
months = [
    "May-21", "Jun-21", "Jul-21", "Aug-21", "Sep-21", "Oct-21", "Nov-21", "Dec-21",
    "Jan-22", "Feb-22", "Mar-22", "Apr-22", "May-22", "Jun-22", "Jul-22", "Aug-22",
    "Sep-22", "Oct-22", "Nov-22", "Dec-22",
    "Jan-23", "Feb-23", "Mar-23", "Apr-23", "May-23"
]

values = [
    9.5, 10.0, 11.0, 12.0, 15.5, 20.0, 22.3, 11.5,
    12.2, 22.2, 24.4, 22.0, 25.9, 22.1, 25.5, 25.4,
    28.4, 29.7, 30.9, 21.1,
    29.4, 33.2, 31.8, 28.6, 29.2
]

occ_df = (
    pd.DataFrame({"Month": months, "occupancy": values})
    .assign(Month=lambda d: pd.to_datetime(d["Month"], format="%b-%y").dt.to_period("M"))
)


# -------------------------
# 2. Passenger flow（月汇总）
# -------------------------
df = pd.read_csv("data/clean/total_data.csv")

monthly_total = (
    df.assign(
        Date=lambda d: pd.to_datetime(d["Date"]),
        total=lambda d: d.drop(columns="Date").sum(axis=1),
        Month=lambda d: d["Date"].dt.to_period("M")
    )
    .groupby("Month", as_index=False)["total"]
    .sum()
)


# -------------------------
# 3. 训练模型
# -------------------------
train = pd.merge(monthly_total, occ_df, on="Month", how="inner")

X = train[["total"]]
y = train["occupancy"]

model = LinearRegression()
model.fit(X, y)

print(f"k = {model.coef_[0]:.6f}, b = {model.intercept_:.6f}")


# -------------------------
# 4. 构造预测区间（未来）
# -------------------------
last_known = occ_df["Month"].max()

future_range = pd.period_range(start=last_known + 1, end="2025-12", freq="M")
future_df = pd.DataFrame({"Month": future_range})

# merge total
future_df = future_df.merge(monthly_total, on="Month", how="left")

# 填充未来 total（如果缺失）
future_df["total"] = future_df["total"].ffill()

# 预测
future_df["occupancy"] = model.predict(future_df[["total"]]).clip(0, 100)


# -------------------------
# 5. 合并历史 + 未来
# -------------------------
history = occ_df.copy()

full_output = pd.concat([history, future_df[["Month", "occupancy"]]], ignore_index=True)


# -------------------------
# 6. 格式整理
# -------------------------
full_output = full_output.assign(
    Month=lambda d: d["Month"].dt.strftime("%b-%y")
)


# -------------------------
# 7. 导出
# -------------------------
full_output.to_csv("office_occupancy.csv", index=False)

print("\n✅ Saved: office_occupancy.csv")