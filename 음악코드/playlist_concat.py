import glob
import pandas as pd

csv_files = glob.glob("playlist_data/youtube_results_*.csv")

df_list = [pd.read_csv(f, encoding="utf-8-sig") for f in csv_files]
merged = pd.concat(df_list, ignore_index=True)

merged.to_csv("playlist_data/playlist_all.csv", index=False, encoding="utf-8-sig")

print(f"총 {len(merged)}개 행을 playlist_data/playlist_all.csv에 저장했습니다.")