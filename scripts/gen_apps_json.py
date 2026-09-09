#!/usr/bin/env python3
"""mgang4u-dev의 *-releases 저장소에서 최신 릴리스를 읽어 apps.json을 생성한다.

에셋 URL은 git.mgang.app(Worker)을 거치게 쓴다. Worker가 mgang4u -> mgang4u-dev로
302 리다이렉트하므로, 저장소 계정이 또 바뀌어도 홈페이지 링크는 그대로 둘 수 있다.
"""
import json
import os
import subprocess
import sys

OWNER = "mgang4u-dev"
LEGACY_OWNER = "mgang4u"          # git.mgang.app 경로에 쓰는 이름
PROXY = "https://git.mgang.app"
SKIP = set()                       # 목록에서 빼고 싶은 저장소 이름
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apps.json")


def api(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def main():
    repos = api(f"users/{OWNER}/repos?per_page=100&type=owner")
    if repos is None:
        sys.exit("저장소 목록을 가져오지 못했습니다")

    apps = []
    for repo in repos:
        name = repo["name"]
        if repo["private"] or not name.endswith("-releases") or name in SKIP:
            continue

        rel = api(f"repos/{OWNER}/{name}/releases/latest")
        if rel is None:          # 릴리스가 아직 없는 저장소는 건너뛴다
            print(f"  skip {name} (릴리스 없음)")
            continue

        tag = rel.get("tag_name", "")
        assets = [
            {
                "name": a["name"],
                "url": f"{PROXY}/{LEGACY_OWNER}/{name}/releases/download/{tag}/{a['name']}",
                "download_count": a.get("download_count", 0),
            }
            for a in rel.get("assets", [])
        ]
        apps.append({
            "name": name,
            "full_name": f"{LEGACY_OWNER}/{name}",
            "description": repo.get("description") or "",
            "html_url": f"{PROXY}/{LEGACY_OWNER}/{name}",
            "tag_name": tag,
            "published_at": rel.get("published_at", ""),
            "assets": assets,
            "downloads": sum(a["download_count"] for a in assets),
        })
        print(f"  {name} {tag} ({len(assets)} assets)")

    if not apps:
        sys.exit("릴리스를 하나도 찾지 못했습니다 — apps.json을 덮어쓰지 않습니다")

    apps.sort(key=lambda a: a["name"])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(apps, f, ensure_ascii=False, indent=4)
        f.write("\n")
    print(f"{len(apps)}개 앱을 {OUT}에 기록했습니다")


if __name__ == "__main__":
    main()
