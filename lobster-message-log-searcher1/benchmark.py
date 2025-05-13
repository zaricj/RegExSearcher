import pandas as pd
import time

csv_path = r"C:\Users\ZaricJ\Documents\05 Entwicklung\Arbeit GitLab\lobster-message-log-searcher\data\CSVData\DataWizard.csv"
export_path = "exported_statistics.xlsx"

start_time = time.time()

# Step 1: Read CSV with optimizations
df = pd.read_csv(
    csv_path,
    engine="pyarrow",  # or engine="c" if pyarrow is unavailable
    usecols=["Filename", "Filesize in Bytes", "Profile Name"],
    dtype={
        "Filename": "string",
        "Filesize in Bytes": "int64",
        "Profile Name": "string"
    }
)

read_duration = time.time()
print(f"CSV read time: {read_duration - start_time:.2f} seconds")

# Step 2: Process statistics (basic example)
summary = df.groupby("Profile Name")["Filesize in Bytes"].agg(["mean", "std", "min", "max", "count"]).reset_index()

summary["mean"] = summary["mean"].round(2)
summary["std"] = summary["std"].round(2)

# Step 3: Export to Excel
with pd.ExcelWriter(export_path, engine="xlsxwriter") as writer:
    summary.to_excel(writer, sheet_name="Profile Stats", index=False)

end_time = time.time()
print(f"Excel export time: {end_time - read_duration:.2f} seconds")
print(f"Total time: {end_time - start_time:.2f} seconds")
