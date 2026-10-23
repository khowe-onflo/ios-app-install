"""Print a JSON summary of an .ipa: app name, bundle id, version, and signing details."""
import json
import plistlib
import re
import sys
import zipfile


def signing_info(raw):
    # embedded.mobileprovision is a CMS-signed blob wrapping an XML plist; pull the plist out directly.
    start, end = raw.find(b"<?xml"), raw.find(b"</plist>")
    if start == -1 or end == -1:
        return {}
    prov = plistlib.loads(raw[start:end + len(b"</plist>")])
    devices = prov.get("ProvisionedDevices")
    if prov.get("ProvisionsAllDevices"):
        kind = "enterprise"
    elif devices is None:
        kind = "app-store"
    elif prov.get("Entitlements", {}).get("get-task-allow"):
        kind = "development"
    else:
        kind = "ad-hoc"
    expires = prov.get("ExpirationDate")
    return {
        "signing": kind,
        "profile": prov.get("Name"),
        "team": prov.get("TeamName"),
        "devices": len(devices) if devices is not None else None,
        # Already public inside the .ipa's profile; listed so the page can check whether a device is included.
        "udids": sorted(devices) if devices is not None else None,
        "profile_expires": expires.isoformat() + "Z" if expires else None,
    }


def main(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        info_path = next(n for n in names if re.fullmatch(r"Payload/[^/]+\.app/Info\.plist", n))
        app_dir = info_path[: -len("Info.plist")]
        info = plistlib.loads(z.read(info_path))
        prov_path = app_dir + "embedded.mobileprovision"
        prov = signing_info(z.read(prov_path)) if prov_path in names else {"signing": "unsigned"}

    meta = {
        "name": info.get("CFBundleDisplayName") or info.get("CFBundleName") or info["CFBundleIdentifier"],
        "bundle_id": info["CFBundleIdentifier"],
        "version": info.get("CFBundleShortVersionString", ""),
        "build": info.get("CFBundleVersion", ""),
        "min_os": info.get("MinimumOSVersion"),
        **prov,
    }
    json.dump(meta, sys.stdout, indent=2)


if __name__ == "__main__":
    main(sys.argv[1])
