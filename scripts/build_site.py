"""Build the Pages site: copy site/, write an OTA manifest per build release, and builds.json for the page."""
import json
import os
import plistlib
import shutil
import sys
from pathlib import Path


def main(releases_path, out_dir):
    out = Path(out_dir)
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(Path(__file__).resolve().parent.parent / "site", out)
    (out / "manifests").mkdir()

    pages = json.loads(Path(releases_path).read_text())  # gh api --paginate --slurp: a list of pages
    builds = []
    for release in (r for page in pages for r in page):
        tag = release["tag_name"]
        if release["draft"] or not tag.startswith("build-"):
            continue
        ipa = next((a for a in release["assets"] if a["name"].endswith(".ipa")), None)
        try:
            meta = json.loads(release["body"] or "")
        except ValueError:
            meta = None
        if not ipa or not meta:
            continue

        manifest = {"items": [{
            "assets": [{"kind": "software-package", "url": ipa["browser_download_url"]}],
            "metadata": {
                "bundle-identifier": meta["bundle_id"],
                "bundle-version": meta["version"] or meta["build"],
                "kind": "software",
                "title": meta["name"],
            },
        }]}
        (out / "manifests" / f"{tag}.plist").write_bytes(plistlib.dumps(manifest))
        builds.append({
            **meta,
            "tag": tag,
            "release_id": release["id"],
            "uploaded": release["created_at"],
            "size": ipa["size"],
        })

    builds.sort(key=lambda b: b["uploaded"], reverse=True)
    (out / "builds.json").write_text(json.dumps({
        "repo": os.environ.get("GITHUB_REPOSITORY", ""),
        "branch": os.environ.get("DEFAULT_BRANCH", "main"),
        "builds": builds,
    }, indent=2))
    print(f"Built site with {len(builds)} build(s)")


if __name__ == "__main__":
    main(*sys.argv[1:3])
