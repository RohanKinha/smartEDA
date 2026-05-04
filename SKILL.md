---
description: How to publish a web project to GitHub and deploy it live on Vercel
---

# Publish to GitHub + Vercel Skill

End-to-end workflow for pushing a web project to GitHub and deploying it live on Vercel with zero hiccups. Incorporates all known gotchas and best practices.

---

## When to Use This Workflow

- User asks to "publish", "deploy", "make live", or "push" a website
- User wants to create a GitHub repo for a project
- User wants to deploy to Vercel
- User says "go live", "host this", or "put it online"
- User wants to update an already-deployed site

---

## Prerequisites

### Required Tools

Verify these are installed and authenticated before starting:

```bash
# GitHub CLI
which gh && gh auth status 2>&1

# Vercel CLI
which vercel && vercel whoami 2>&1
```

### If GitHub CLI is NOT installed

```bash
brew install gh
gh auth login --web --git-protocol https
```

> Enter a device code at `github.com/login/device`. Wait for `✓ Logged in` confirmation before proceeding.
> 

### If Vercel CLI is NOT installed or NOT authenticated

```bash
npm i -g vercel
vercel login
```

> Enter a device code at `vercel.com/device`. Wait for `Congratulations! You are now signed in.` confirmation before proceeding.
> 

---

## Workflow Checklist

```
- [ ] Step 1: Pre-flight checks (tools + auth)
- [ ] Step 2: Prepare project for deployment
- [ ] Step 3: Create GitHub repository
- [ ] Step 4: Commit and push code
- [ ] Step 5: Deploy to Vercel
- [ ] Step 6: Verify deployment
- [ ] Step 7: Report to user
```

---

## Instructions

### Step 1: Pre-Flight Checks

Run these checks **before** doing anything else:

```bash
gh auth status 2>&1
vercel whoami 2>&1
```

If either is not authenticated, follow the prerequisite steps above. **Do NOT proceed until both are authenticated.**

---

### Step 2: Prepare Project for Deployment

This is the **most critical step** — skipping this causes deployment failures.

### 2a: Static Assets → `public/` Directory

> ⚠️ **Critical for Vite/React:** Static assets (images, logos, fonts, favicons) **must** be in the `public/` directory. Files in the project root are NOT served as static files in production.
> 

```bash
mkdir -p public

find . -maxdepth 1 -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.svg" -o -name "*.gif" -o -name "*.ico" -o -name "*.webp" -o -name "*.woff" -o -name "*.woff2" -o -name "*.ttf" \) ! -path "./node_modules/*" -exec cp {} public/ \;
```

**Check component references** — verify that any `<img src="/filename.ext">` references have the corresponding file in `public/`:

```bash
grep -rn 'src="/' --include="*.tsx" --include="*.jsx" --include="*.html" --include="*.ts" --include="*.js" . | grep -v node_modules
```

### 2b: Environment Variables

Check if the project uses environment variables:

```bash
grep -rn 'import.meta.env\|process.env\|VITE_' --include="*.tsx" --include="*.ts" --include="*.jsx" --include="*.js" . | grep -v node_modules | head -20
```

If env vars are found, note them — they'll need to be set in Vercel during Step 5.

### 2c: Build Test

```bash
npm run build 2>&1
```

Common build failures:

- **TypeScript errors** → Fix type issues or add `// @ts-ignore` for non-critical ones
- **Missing dependencies** → `npm install <package>`
- **Import errors** → Check file paths and case sensitivity

### 2d: Verify `.gitignore`

Ensure these entries exist:

```
node_modules/
dist/
.vercel/
.env
.env.local
.env.*.local
```

---

### Step 3: Create GitHub Repository

### 3a: Check for existing git repo

```bash
git remote -v 2>&1
```

### 3b: If NO repo exists, initialize one

```bash
git init
git add -A
git commit -m "Initial commit"
```

### 3c: Create the GitHub repo

Use a clean, descriptive repo name (lowercase, hyphens):

```bash
# Public repo (recommended for Vercel free tier)
gh repo create my-project-name --public --source=. --push --description "Project description"

# Private repo
gh repo create my-project-name --private --source=. --push --description "Project description"
```

### 3d: If repo already exists but remote is wrong

> ⚠️ **Gotcha:** Cloned projects retain the original `origin` remote. `gh repo create` will fail with "Unable to add remote" if `origin` already exists.
> 

```bash
# Create repo first (without --source and --push)
gh repo create my-project-name --public --description "Project description"

# Update the remote
git remote set-url origin https://github.com/YOUR_USERNAME/my-project-name.git

# Push
git push -u origin main --force
```

---

### Step 4: Commit and Push Code

```bash
git add -A
git status
git commit -m "feat: descriptive message about what changed"
git push origin main
```

**Commit message conventions:**

| Prefix | Use Case |
| --- | --- |
| `feat:` | New features / initial commits |
| `fix:` | Bug fixes |
| `chore:` | Config / dependency changes |
| `style:` | UI / design tweaks |

---

### Step 5: Deploy to Vercel

### 5a: Deploy with auto-detection

```bash
vercel --yes --prod 2>&1
```

This will auto-detect the framework, link the project to your Vercel account, connect the GitHub repo for auto-deployments, and build + deploy to production.

### 5b: Set environment variables (if needed)

**Using Vercel MCP (preferred):**

```
mcp_vercel_vercel_create_env_var:
  projectId: my-project-name
  key: ENV_VAR_NAME
  value: ENV_VAR_VALUE
  target: ["production", "preview", "development"]
```

**Using CLI:**

```bash
vercel env add VARIABLE_NAME production
```

After adding env vars, trigger a redeploy:

```bash
vercel --prod 2>&1
```

### 5c: Verify deployment status

```
mcp_vercel_vercel_list_deployments:
  projectId: my-project-name
  limit: 1
  state: READY
```

---

### Step 6: Verify Deployment

The Vercel output will show a **Production URL** and an **Inspect URL**.

Verify the following:

- [ ]  Page loads without errors
- [ ]  Images and logos display correctly
- [ ]  No console errors
- [ ]  Layout looks correct on mobile and desktop

---

### Step 7: Report to User

```
✅ Website Published Successfully!

| Detail             | Value                                          |
|--------------------|------------------------------------------------|
| Live URL           | https://my-project-name.vercel.app             |
| GitHub Repository  | https://github.com/USERNAME/my-project-name    |
| Deployment Status  | READY ✅                                        |
| Framework          | Vite / Next.js / etc.                          |
| Auto-Deploy        | Enabled (pushes to main auto-deploy)           |
```

---

## Updating an Already-Deployed Site

If the site is already on Vercel and connected to GitHub:

```bash
git add -A
git commit -m "fix: describe what changed"
git push origin main
```

Vercel will auto-redeploy within ~15 seconds. Verify with:

```
mcp_vercel_vercel_list_deployments:
  projectId: my-project-name
  limit: 1
```

---

## Error Handling

### Common Errors & Fixes

| Error | Cause | Fix |
| --- | --- | --- |
| `Unable to add remote "origin"` | Cloned project already has `origin` | `git remote set-url origin NEW_URL` |
| Broken images on Vercel | Static files not in `public/` | Move all static assets to `public/` |
| `gh: not found` | GitHub CLI not installed | `brew install gh` |
| `vercel: command not found` | Vercel CLI not installed | `npm i -g vercel` |
| Vercel device code prompt | CLI not authenticated | Enter code at `vercel.com/device` |
| GitHub device code prompt | CLI not authenticated | Enter code at `github.com/login/device` |
| Build fails on Vercel | TypeScript / dependency errors | Run `npm run build` locally first |
| `BUILDING` state stuck | Large project or slow deps | Wait up to 5 min, then check dashboard |
| Env vars not available | Not set in Vercel | Add via MCP or `vercel env add` |
| 404 on page refresh (SPA) | Missing rewrite rules | Add `vercel.json` with rewrites |

---

### Framework-Specific Gotchas

### Vite

1. **Static assets must be in `public/`** — the #1 deployment issue
2. **`base` in `vite.config.ts`** — should be `'/'` for Vercel (default is fine)
3. **SPA routing** — add `vercel.json` with rewrites if using client-side routing:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### Next.js

1. **Static exports** — if using `output: 'export'`, set output directory in Vercel
2. **API routes** — work automatically on Vercel as serverless functions
3. **Image optimization** — works out of the box on Vercel

---

## Quick Reference: Full Deploy in 3 Steps

For a project that's already prepared (static assets in `public/`, builds clean):

```bash
# 1. Create GitHub repo + push
gh repo create my-project-name --public --source=. --push --description "Project description"

# 2. Deploy to Vercel
vercel --yes --prod

# 3. Done! Auto-deploys enabled. Future updates:
git add -A && git commit -m "update: description" && git push origin main
```
