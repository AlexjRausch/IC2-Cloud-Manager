# Push Instructions - OAuth Token Limitation

## Issue

The current OAuth token doesn't have the `workflow` scope required to push changes that include `.github/workflows/` files.

## Solution Options

### Option 1: Push via GitHub Web Interface (Recommended)

1. **Go to GitHub**:
   - Visit: https://github.com/AlexjRausch/IC2-Cloud-Manager

2. **Upload Files**:
   - Click **Add file** > **Upload files**
   - Drag and drop ALL modified files from your local repository
   - Or use the GitHub web editor to manually update files

3. **Files to Upload/Update**:
   ```
   .dockerignore
   .gitignore
   app.py
   docker-compose.yml
   index.html
   requirements.txt
   .gitlab-ci.yml
   DEPLOYMENT-GUIDE.md
   SANDBOX-README.md
   docker-compose-portainer.yml
   docker-compose-sandbox.yml
   portainer-ic2-sandbox.yml
   ```

4. **Commit Message**:
   ```
   Add IC2-Sandbox: Write operations, user management, and group locking

   Features: IC2 write ops, encrypted user management, group locking
   ```

5. **Update Workflow (IMPORTANT)**:
   - Edit `.github/workflows/docker-publish.yml`
   - Find the `tags:` section (around line 38)
   - Add this line after `type=raw,value=latest`:
   ```yaml
   type=raw,value=sandbox
   ```
   - Commit the change

### Option 2: Use Personal Access Token

1. **Create New Token**:
   - Go to: https://github.com/settings/tokens
   - Click **Generate new token** > **Generate new token (classic)**
   - Select scopes:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)
   - Generate and copy the token

2. **Update Git Remote**:
   ```bash
   git remote set-url origin https://YOUR_NEW_TOKEN@github.com/AlexjRausch/IC2-Cloud-Manager.git
   ```

3. **Push**:
   ```bash
   git push origin main
   ```

### Option 3: Push Without Workflow Changes

If you just want to get the code live NOW without the workflow changes:

```bash
# This will trigger the existing workflow (without 'sandbox' tag)
# The 'latest' tag will still be built

# No additional steps needed - just deploy with 'latest' tag
```

Update `portainer-ic2-sandbox.yml` to use:
```yaml
image: ghcr.io/alexjrausch/ic2-cloud-manager:latest
```

Instead of:
```yaml
image: ghcr.io/alexjrausch/ic2-cloud-manager:sandbox
```

## Current Status

✅ All code changes committed locally
✅ Ready to push to GitHub
❌ Cannot push due to OAuth token scope limitation

## Quick Deploy Option

**If you want to deploy RIGHT NOW**:

1. The container image `ghcr.io/alexjrausch/ic2-cloud-manager:latest` might already exist from previous builds

2. Use the `portainer-ic2-sandbox.yml` file AS-IS in Portainer:
   - It's configured to use `:sandbox` tag
   - Once you push via web interface, the workflow will build the sandbox tag

3. Or temporarily change to `:latest` tag:
   - Edit `portainer-ic2-sandbox.yml`
   - Change `image:` line to use `:latest`
   - Deploy in Portainer
   - Later switch back to `:sandbox` after workflow is updated

## Recommended Flow

1. **Use GitHub Web Interface** to upload all files
2. **Manually edit** `.github/workflows/docker-publish.yml` to add sandbox tag
3. **Wait** for GitHub Actions to build both `latest` and `sandbox` images
4. **Deploy** to Portainer using `portainer-ic2-sandbox.yml`

## Files Ready for Upload

All these files are in your local repository at:
`/Users/alexvm/Desktop/peplink-clean/`

Simply drag them to GitHub's upload interface!

## What Happens After Push?

1. **GitHub Actions triggers**:
   - Builds Docker image
   - Pushes to ghcr.io with tags: `latest` (and `sandbox` if workflow updated)

2. **Deploy to Portainer**:
   - Use `portainer-ic2-sandbox.yml`
   - Create new stack: `ic2-sandbox`
   - Image will auto-pull from ghcr.io

3. **Access Application**:
   - URL: https://ic2-sandbox.144.202.49.82.nip.io
   - Login: alex / hyrox
   - Test new features!

## Need Help?

All changes are safely committed locally. Your work won't be lost. Choose whichever push method works best for you!
