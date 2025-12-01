from src.drive_loader import load_single_from_drive

file_id = "1Xdqqdb-7DVO2bE151r5zr5lwGqbum7cV"

df = load_single_from_drive(file_id, sheet_name=0)

print("Rows:", len(df))
print(df.head())
