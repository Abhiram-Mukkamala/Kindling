# Seed Demo Repo Guide

To showcase Kindling during the hackathon demo, you will want a small demo repository with realistic signals for the AI crew.

## Recommended Demo Repo Structure
```
demo-repo/
├── README.md              # Project overview with a missing section (e.g. no setup/testing docs)
├── package.json           # Or pyproject.toml / requirements.txt
├── src/
│   ├── index.js           # Or app.py
│   ├── utils.js           # Contains a TODO: "TODO: validate email format before saving"
│   └── api.js             # Contains a FIXME: "FIXME: handle 404 response on user lookup"
```

## Recommended GitHub Issues to Create in Advance
1. Issue 1: "Fix the bug" (Vague title and empty description - perfect for Kindling to identify or contrast).
2. Issue 2: "Add dark mode" (Short description: "Please add dark mode to settings").

## UI Bug for Screenshot Demo
Create a simple UI glitch (e.g. overlapping button or broken margin) in the web app that you can screenshot.
When fed to the Vision model (`VISION_MODEL`), it will produce a clean, scoped issue.
