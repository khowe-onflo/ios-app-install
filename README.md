# iOS OTA builds on GitHub Pages

Upload an `.ipa` from the web page and get an install link and QR code a minute later. Delete builds from the same page when you're done testing.

## How it works

1. The page (`site/index.html`) commits the `.ipa` to a temporary `upload` branch using your GitHub token.
2. The `ingest` job in `.github/workflows/ota.yml` reads the app info (`scripts/ipa_info.py`) and publishes the `.ipa` as a GitHub Release. Release files don't count toward repo size. It then deletes the `upload` branch so the binary doesn't stay in git history.
3. The `deploy` job (`scripts/build_site.py`) writes `manifests/<tag>.plist` and `builds.json` for every build release, then deploys Pages.
4. **Delete** on the page removes the release and its tag, then redeploys.

## One-time setup

1. Create a **public** GitHub repo and push this folder to `main`.
2. Go to **Settings → Pages → Build and deployment → Source** and choose **GitHub Actions**.
3. Go to **Actions → OTA → Run workflow** to do the first deploy. The site appears at `https://<you>.github.io/<repo>/`.
4. Create a [fine-grained token](https://github.com/settings/personal-access-tokens/new) that has access only to this repo, with these permissions:
   - **Contents:** Read and write
   - **Actions:** Read and write
   - **Workflows:** Read and write. GitHub can require this when the page creates the `upload` branch, because that branch also contains `.github/workflows/`.
5. On the site, click **Manage**, paste the token and click **Save**. The token is stored only in that browser.

## Limits and notes

- Maximum `.ipa` size is **100 MB**, the GitHub git blob API limit.
- Builds must be signed **Ad Hoc**, **Development** or **Enterprise**. Ad Hoc and Development builds install only on devices whose UDID is in the provisioning profile. The page shows the signing type and device count and warns about App Store–signed builds and expired profiles.
- Anyone with the link can download the `.ipa`, because the repo is public. Installing still depends on the signing.
- Only someone with a token can upload or delete. Testers only see the builds and Install buttons.
- Testers must open the install link in **Safari** on the iPhone or iPad.
