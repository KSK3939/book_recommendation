import pandas as pd

main_csv = pd.read_csv('data/yes24_steadyseller_국가통합.csv')
genre_csv = pd.read_csv('data/yes24_steadyseller_장르.csv')

genre_dedup = genre_csv.drop_duplicates(subset="ISBN")
merged = main_csv.merge(genre_dedup[["ISBN", "장르"]], on="ISBN", how="left")

merged["장르"] = merged["장르"].fillna("")
merged = merged.dropna(subset=["설명", "ISBN"])  # ISBN NaN도 같이 제거
merged["ISBN"] = merged["ISBN"].astype(int)

merged.to_csv('data/final_merge.csv', index=False, encoding="utf-8-sig")