"""
playlist_auto_crawling.py
장르별 키워드로 유튜브를 검색해 플레이리스트 결과를 수집하고
playlist_data/playlist_all.csv에 추가(append)합니다.

설치:
    pip install yt-dlp

실행:
    python playlist_auto_crawling.py
"""

import csv
import os
import re
import yt_dlp
import pandas as pd

PLAYLIST_CSV = "../playlist_data/playlist_crawl.csv"

# 장르별 유튜브 검색 쿼리 (playlist_all.csv의 genre 값과 동일하게 맞춤)
GENRE_QUERIES = {
    "추리, 미스터리": [
        "추리 미스터리 책 읽을 때 듣기 좋은 플레이리스트",
        "미스터리 소설 집중 BGM 플레이리스트",
    ],
    "SF": [
        "SF 공상과학 책 읽을 때 듣기 좋은 플레이리스트",
        "사이버펑크 SF 음악 플레이리스트",
    ],
    "로맨스": [
        "로맨스 소설 읽을 때 듣기 좋은 플레이리스트",
        "감성 발라드 독서 플레이리스트",
    ],
    "공포, 스릴러": [
        "공포 스릴러 책 읽을 때 듣기 좋은 플레이리스트",
        "긴장감 서스펜스 BGM 플레이리스트",
    ],
    "판타지": [
        "판타지 소설 읽을 때 듣기 좋은 플레이리스트",
        "판타지 OST 모음 플레이리스트",
    ],
    "역사": [
        "역사 소설 책 읽을 때 듣기 좋은 플레이리스트",
        "클래식 오케스트라 독서 플레이리스트",
    ],
    "기타": [
        "독서할 때 듣기 좋은 음악 플레이리스트",
        "책 읽을 때 집중 BGM 플레이리스트",
    ],
}


def format_duration(seconds) -> str:
    """초 → 'n시간 n분 n초' 변환"""
    if not seconds:
        return ""
    seconds = int(seconds)
    hours, r = divmod(seconds, 3600)
    minutes, secs = divmod(r, 60)
    parts = []
    if hours:    parts.append(f"{hours}시간")
    if minutes:  parts.append(f"{minutes}분")
    if secs or not parts: parts.append(f"{secs}초")
    return " ".join(parts)


def search_videos(query: str, max_results: int = 10) -> list:
    """
    유튜브 검색어로 영상 검색 (재생목록/광고 제외, 30분 이하 제외)

    Returns:
        list[dict]: [{"title", "duration", "url"}, ...]
    """
    fetch_count = max_results * 3
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "no_warnings": True,
    }

    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{fetch_count}:{query}", download=False)
        for entry in info.get("entries", []):
            if entry is None:
                continue
            if entry.get("_type") == "playlist" or entry.get("ie_key") == "YoutubePlaylist":
                continue

            video_id = entry.get("id")
            duration = entry.get("duration") or 0

            if not video_id:
                continue
            if duration < 1800:  # 30분 이하 제외
                continue

            results.append({
                "title":    entry.get("title", ""),
                "duration": format_duration(duration),
                "url":      f"https://www.youtube.com/watch?v={video_id}",
            })

            if len(results) >= max_results:
                break

    return results


def crawl_all_genres(max_per_query: int = 10):
    """
    GENRE_QUERIES의 모든 장르/쿼리를 순회하며 수집 후
    playlist_all.csv에 중복 없이 append 합니다.
    """
    os.makedirs(os.path.dirname(PLAYLIST_CSV), exist_ok=True)

    # 기존 URL 목록 로드 (중복 방지)
    existing_urls = set()
    if os.path.isfile(PLAYLIST_CSV):
        try:
            df_exist = pd.read_csv(PLAYLIST_CSV)
            existing_urls = set(df_exist["url"].dropna().tolist())
            print(f"기존 항목 {len(existing_urls)}개 로드 완료\n")
        except Exception:
            pass

    fieldnames = ["genre", "title", "duration", "url"]
    new_rows = []

    for genre, queries in GENRE_QUERIES.items():
        for query in queries:
            print(f"[{genre}] 검색: {query}")
            videos = search_videos(query, max_results=max_per_query)
            added = 0
            for v in videos:
                if v["url"] in existing_urls:
                    continue
                row = {"genre": genre, **v}
                new_rows.append(row)
                existing_urls.add(v["url"])
                added += 1
            print(f"  → {added}개 추가 (검색 결과 {len(videos)}개)\n")

    if not new_rows:
        print("추가할 새 항목이 없습니다.")
        return

    # CSV append
    file_exists = os.path.isfile(PLAYLIST_CSV)
    with open(PLAYLIST_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)

    print(f"총 {len(new_rows)}개 항목을 {PLAYLIST_CSV}에 추가했습니다.")


if __name__ == "__main__":
    crawl_all_genres(max_per_query=10)