---
name: viral-facebook-reel-maker
description: Create branded vertical Facebook Reels end to end from a reference social channel, local footage, music, logos, and source content. Use when Codex should analyze a sample channel, initialize a reusable media workspace, identify high-performing content patterns, write or preserve on-video text and captions, rotate unused footage, render 9:16 captioned videos with music and contextual logos, validate previews, open Facebook or Meta Business Suite, request browser connection or sign-in, upload a Reel, and prepare or schedule publishing after final user approval.
---

# Viral Facebook Reel Maker

Build a reusable production system for any brand. Keep all customer identity, content, media, credentials, and publishing state outside this skill.

## Core contract

1. Treat the user's latest instructions as authoritative.
2. Never copy claims, identity, private media, or voice from the reference channel. Learn structural patterns only.
3. Never inspect or store passwords, cookies, OTP codes, access tokens, or payment data.
4. Prepare the complete Reel, caption, destination page, and schedule before requesting final approval.
5. Require explicit final approval immediately before clicking Publish or Schedule. Do not enable boosts, ads, or paid options.
6. Preserve source text verbatim when `content_mode` is `verbatim`; only line wrapping may change.
7. Keep source footage unchanged. Write all outputs and ledgers to the generated workspace.

## Route the request

- For first-time setup or a supplied sample channel, follow **Onboard a brand**.
- For “make the next video,” follow **Produce the next Reel**.
- For revisions, modify only the requested element, render again, and re-run visual checks.
- For publishing or scheduling, follow **Publish through the browser**.
- For a request to open media folders, open the generated workspace or requested subfolder in the operating system.

## Onboard a brand

1. Ask only for missing essentials that cannot be inferred safely: reference-channel URL, destination page, workspace location, and whether the user will supply footage, music, and logos.
2. If browser tools are available, open the reference channel. Request sign-in only when access is blocked. Never ask the user to paste credentials into chat.
3. Collect observable examples and metrics. Distinguish visible facts from inferences. Do not claim content is viral without supporting engagement evidence.
4. Derive reusable patterns: topics, hooks, structures, text density, visual hierarchy, caption length, endings, and posting cadence. Do not imitate distinctive wording.
5. Create a workspace with `python scripts/setup_workspace.py --root <folder> --brand-name <name> --reference-url <url> --destination-url <url>`.
6. Write confirmed settings to `BRAND_CONFIG.json`. Keep uncertain values `null` and ask only when they block production.
7. Open `01_VIDEO_GOC`, `02_NHAC_NEN`, and `03_LOGO` so the user can add assets. Continue automatically after assets are present.
8. Read [references/CHANNEL_ANALYSIS.md](references/CHANNEL_ANALYSIS.md) for the analysis schema and selection rules.

## Produce the next Reel

1. Read `BRAND_CONFIG.json`, `07_NHAT_KY/media_usage.csv`, and `07_NHAT_KY/publishing_schedule.csv`.
2. Select unused source media with `python scripts/select_media.py --workspace <folder> --kind video` and repeat for music or logo as needed.
3. Reject items marked `blocked` in the ledgers.
4. Prepare a content JSON file. Use `verbatim` for approved source text and `adapted` only when rewriting is authorized. Follow [references/CONTENT_AND_CAPTION.md](references/CONTENT_AND_CAPTION.md).
5. Render with `python scripts/render_reel.py --workspace <folder> --content <content.json>`.
6. Validate with `python scripts/validate_output.py --video <output.mp4> --duration <seconds>`.
7. Inspect generated previews visually at several timestamps when the subject moves. Follow [references/VISUAL_QA.md](references/VISUAL_QA.md).
8. If text overflows, a logo covers the subject, contrast is weak, or spacing is uneven, adjust and rerender without asking the user to diagnose the technical cause.
9. Present the final video and caption for review. Do not publish yet.
10. Update the usage ledger only after a successful render; never mark a failed attempt as used.

## Default video behavior

- Produce H.264/AAC MP4, 1080x1920, 30 fps, `yuv420p`, with fast-start.
- Default to 20 seconds, 0.5x footage speed, darkened background, and a short audio fade-out.
- Display approved text as one fixed block for the full video when `show_full_text` is true.
- Use natural upper/lowercase, white text, and a matte yellow-lime highlight without glow or outline unless configured otherwise.
- Place a topical logo only when it adds context. Scale proportionally; place it in a verified empty region aligned with the content block; never cover a face, eyes, hands, key objects, or text.
- Rotate through unused footage before reusing clips. Never use the same source for consecutive outputs.

## Publish through the browser

1. Prefer a purpose-built connector or API when available and authorized. Otherwise use the Browser skill; use Computer Use only for desktop UI the browser cannot operate.
2. Open the destination page or Meta Business Suite.
3. If the browser is not connected, guide the user to connect it. If Facebook requires authentication, open sign-in and ask the user to sign in there; never handle credentials.
4. Verify the selected page by visible page name and destination URL.
5. Open the Reel composer, upload the approved MP4, insert the approved caption, and verify the post remains a Reel.
6. Read [references/PUBLISHING.md](references/PUBLISHING.md). Find the next open slot while respecting configured times and daily limit; advance to the next day when full.
7. Stop with a concrete summary: page, filename, caption opening, date, time, timezone, and mode. Ask for explicit approval.
8. After approval, click Publish or Schedule, verify success, and append the result to `07_NHAT_KY/publishing_schedule.csv`.
9. If copyright, processing, or upload warnings appear, preserve the draft, report the exact warning, and replace media only when authorized.

## Resource map

- Read [references/CHANNEL_ANALYSIS.md](references/CHANNEL_ANALYSIS.md) for reference-channel analysis and ranking.
- Read [references/CONTENT_AND_CAPTION.md](references/CONTENT_AND_CAPTION.md) for content modes and captions.
- Read [references/VISUAL_QA.md](references/VISUAL_QA.md) for typography, logo placement, and previews.
- Read [references/PUBLISHING.md](references/PUBLISHING.md) for connection, scheduling, and approval.
- Use `assets/default-config.json` as the portable baseline.

## Failure handling

- If FFmpeg or FFprobe is missing, report the dependency and exact PATH correction needed.
- If footage or music is missing, open the corresponding folder and state what is needed.
- If a platform layout changes, inspect the current UI instead of using memorized coordinates.
- If browser connection is unavailable, explain how to enable Computer use or connect a supported browser; complete all local artifacts first.
- Keep drafts and logs recoverable. Never delete user media to fix an error.
