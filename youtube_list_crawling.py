
import csv
import re
import yt_dlp


def search_youtube_videos(query: str, max_results: int = 10):
    # 유튜브에서 검색어로 영상 결과만 반환합니다.
    # 여유있게 더 많이 가져온 뒤 필터링 (재생목록 등 섞여 있을 수 있음)
    fetch_count = max_results * 3

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,   # 빠른 메타데이터만 (영상 다운로드 안 함)
        "skip_download": True,
        "no_warnings": True,
    }

    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_result = ydl.extract_info(f"ytsearch{fetch_count}:{query}", download=False)

        for entry in search_result.get("entries", []):
            if entry is None:
                continue

            # 재생목록(playlist) 결과 제외 — ie_key가 'YoutubePlaylist'이거나 _type이 'playlist'인 경우
            if entry.get("_type") == "playlist" or entry.get("ie_key") == "YoutubePlaylist":
                continue
            video_id = entry.get("id")
            if not video_id:
                continue
            # 30분(1800초) 이하 영상은 제외
            duration = entry.get("duration") or 0
            if duration <= 1800:
                continue


            results.append({
                "title": entry.get("title", ""),
                "duration": entry.get("duration") or "",
                "url": f"https://www.youtube.com/watch?v={video_id}",
            })

            if len(results) >= max_results:
                break

    return results


def format_duration(seconds):
    # 초 단위를 'n시간 n분 n초' 문자열로 변환
    if seconds == "" or seconds is None:
        return ""

    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}시간")
    if minutes > 0:
        parts.append(f"{minutes}분")
    if secs > 0 or not parts:
        parts.append(f"{secs}초")

    return " ".join(parts)


def save_to_csv(rows: list, filepath: str):
    if not rows:
        print("저장할 데이터가 없습니다.")
        return

    fieldnames = ["genre", "title", "duration", "url"]

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)}개 항목을 {filepath}에 저장했습니다.")

def crawl_by_genre(genre_label: str, query: str, max_results: int = 10, output_path: str = None):
# genre column에 지정한 장르 라벨을 일괄 적용해 CSV로 저장
    if output_path is None:
        safe_query = re.sub(r'[\\/*?:"<>| ]', "_", query)
        output_path = f"playlist_data/youtube_results_{safe_query}.csv"

    print(f"검색어: {query}")
    videos = search_youtube_videos(query, max_results=max_results)
    print(f"  -> {len(videos)}개 영상 수집")

    rows = [
        {   "genre": genre_label,
            "title": v["title"],
            "duration": format_duration(v["duration"]),
            "url": v["url"],}
        for v in videos
    ]
    save_to_csv(rows, output_path)

    return output_path


if __name__ == "__main__":
    genre_label = "추리, 미스터리"
    query = "추리 미스터리 책 읽을 때 듣기 좋은 음악"
    n = 10

    output_file = crawl_by_genre(genre_label, query, max_results=n)
    print(f"\n완료: {output_file}")