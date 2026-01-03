# IC2-Sandbox Deployment Guide

Complete step-by-step guide to deploy the IC2-Sandbox container via GitHub Actions to Portainer.

## Overview

This deployment will create a new container called `IC2-Sandbox` running at `https://ic2-sandbox.144.202.49.82.nip.io` with full write capabilities and new features:
- ✅ IC2 write operations enabled
- ✅ Encrypted user management
- ✅ Group locking feature
- ✅ No "READ-ONLY MODE" badge

## Prerequisites

- GitHub repository with Actions enabled
- Portainer instance running
- Access to Traefik reverse proxy
- Network: `sso_sso_network`

## Step 1: Push to GitHub

All changes are ready in your local repository. Push to GitHub to trigger the automated build:

```bash
# Check current status
git status

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Add IC2-Sandbox: Write operations, user management, and group locking

Features added:
- Fernet encryption for password storage
- User management API and UI
- Group locking mechanism
- IC2 API write operations (POST/PUT/DELETE)
- Removed READ-ONLY MODE badge
- Persistent data volumes for sandbox testing

New files:
- portainer-ic2-sandbox.yml (Portainer deployment)
- SANDBOX-README.md (Feature documentation)
- DEPLOYMENT-GUIDE.md (This file)

Modified files:
- app.py (encryption, user mgmt, IC2 write ops)
- index.html (UI for user mgmt and group locks)
- requirements.txt (added cryptography)
- .gitlab-ci.yml (multi-tag build support)
- .gitignore/.dockerignore (secure file exclusions)"

# Push to GitHub (triggers GitHub Actions workflow)
git push origin main
```

## Step 2: Monitor GitHub Actions

1. Go to your GitHub repository: https://github.com/AlexjRausch/IC2-Cloud-Manager
2. Navigate to **Actions** tab
3. Watch the workflow progress:
   - **Build and Publish Docker Container** workflow will run
   - Docker image is built and pushed to GitHub Container Registry (ghcr.io)

Expected output:
```
✓ Build and push Docker image
Successfully tagged ghcr.io/alexjrausch/ic2-cloud-manager:latest
Successfully tagged ghcr.io/alexjrausch/ic2-cloud-manager:sandbox
```

## Step 3: Get the Image Path

After the build completes, your image will be available at:

```
ghcr.io/alexjrausch/ic2-cloud-manager:sandbox
```

Or use:
```
ghcr.io/alexjrausch/ic2-cloud-manager:latest
```

**Find your exact path:**
1. GitHub: Go to your repository
2. Look for **Packages** on the right sidebar
3. Click on the package to see all tags

## Step 4: Deploy to Portainer

### Option A: Using Portainer UI (Recommended)

1. **Login to Portainer** at your Portainer URL

2. **Create New Stack**
   - Navigate to **Stacks**
   - Click **+ Add stack**
   - Name: `ic2-sandbox`

3. **Paste the Compose File**
   - Use the contents of `portainer-ic2-sandbox.yml`
   - The image is already set to:
   ```yaml
   image: ghcr.io/alexjrausch/ic2-cloud-manager:sandbox
   ```

4. **Set Environment Variables** (Optional)
   - Click **+ Add environment variable**
   - Add any custom variables:
     ```
     PEPLINK_CLIENT_ID=your-client-id
     PEPLINK_CLIENT_SECRET=your-client-secret
     GITHUB_REGISTRY_IMAGE=ghcr.io/alexjrausch/ic2-cloud-manager:sandbox
     ```

5. **Deploy the Stack**
   - Click **Deploy the stack**
   - Wait for container to start (check health status)

### Option B: Using Portainer API/CLI

```bash
# Set your Portainer details
PORTAINER_URL="https://your-portainer-url"
PORTAINER_TOKEN="your-api-token"
STACK_NAME="ic2-sandbox"

# Deploy stack via API
curl -X POST "${PORTAINER_URL}/api/stacks" \
  -H "X-API-Key: ${PORTAINER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @portainer-stack-payload.json
```

## Step 5: Verify Deployment

### Check Container Status

1. **Portainer Dashboard**
   - Go to **Containers**
   - Find `IC2-Sandbox`
   - Status should be: 🟢 **Running**

2. **Check Logs**
   ```
   Click on IC2-Sandbox > Logs
   ```

   Look for:
   ```
   [API] Authenticated successfully
   [SERVER] Running at http://localhost:8000
   ```

3. **Health Check**
   - Should show: ✅ **Healthy**

### Test the Application

1. **Access the URL**
   ```
   https://ic2-sandbox.144.202.49.82.nip.io
   ```

2. **Login**
   - Username: `alex`
   - Password: `hyrox`

3. **Verify New Features**
   - ✅ No "READ-ONLY MODE" badge in header
   - ✅ "Users" button visible in top banner
   - ✅ Lock icons (🔓) next to each group
   - ✅ Click "Users" to see user management

4. **Test User Management**
   - Click "Users" button
   - Add a test user
   - Change password
   - Delete test user

5. **Test Group Locking**
   - Click lock icon next to any group
   - Should toggle between 🔒 (locked) and 🔓 (unlocked)

## Step 6: Verify Data Persistence

```bash
# Connect to container
docker exec -it IC2-Sandbox sh

# Check files exist
ls -la /app/.encryption_key
ls -la /app/.users_db.json
ls -la /app/.locked_groups.json

# Exit container
exit
```

Expected files:
- `.encryption_key` - Encryption key (600 permissions)
- `.users_db.json` - Encrypted user database (600 permissions)
- `.locked_groups.json` - Group lock status

## Troubleshooting

### Container Won't Start

**Check Logs:**
```bash
docker logs IC2-Sandbox
```

**Common Issues:**
1. **Port conflict**: Port 8000 already in use
2. **Network issue**: `sso_sso_network` doesn't exist
3. **Image pull fail**: Registry authentication issue

### Cannot Access URL

**Check Traefik:**
1. Ensure Traefik is running
2. Check Traefik logs for routing errors
3. Verify DNS: `ic2-sandbox.144.202.49.82.nip.io` resolves correctly

**Check Labels:**
```bash
docker inspect IC2-Sandbox | grep traefik
```

### Login Fails

**Reset to Default:**
```bash
# Stop container
docker stop IC2-Sandbox

# Remove user database
docker exec IC2-Sandbox rm /app/.users_db.json

# Restart container (will recreate with defaults)
docker restart IC2-Sandbox
```

Default credentials: `alex` / `hyrox`

### Lost Encryption Key

**If encryption key is lost:**
```bash
# This will reset all encrypted data
docker exec IC2-Sandbox rm /app/.encryption_key /app/.users_db.json
docker restart IC2-Sandbox
```

**⚠️ WARNING**: This deletes all user data!

## Updating the Sandbox

### Automatic Updates (Watchtower)

If you have Watchtower running:
```bash
# Force check for updates
docker exec watchtower watchtower --run-once
```

### Manual Update

```bash
# Pull latest image
docker pull registry.gitlab.com/YOUR-USERNAME/YOUR-REPO:sandbox

# Recreate container (Portainer will handle this)
# Or manually:
docker-compose -f portainer-ic2-sandbox.yml pull
docker-compose -f portainer-ic2-sandbox.yml up -d
```

### Update from GitHub

1. Make code changes locally
2. Commit and push to GitHub
3. Wait for GitHub Actions workflow to complete
4. Update container in Portainer:
   - **Stacks > ic2-sandbox > Update the stack**
   - Enable: **Re-pull image and redeploy**
   - Click **Update**

## Security Considerations

### Important Files

These files contain sensitive data and should be backed up:

1. **`.encryption_key`**
   - Fernet encryption key
   - **⚠️ NEVER lose this file or all passwords are lost**
   - Backup location: `/var/lib/docker/volumes/ic2-sandbox-data/_data/`

2. **`.users_db.json`**
   - Encrypted user database
   - Can be regenerated if encryption key exists

3. **`.locked_groups.json`**
   - Group lock status
   - Can be safely deleted (groups become unlocked)

### Backup Commands

```bash
# Backup volume data
docker run --rm -v ic2-sandbox-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/ic2-sandbox-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore from backup
docker run --rm -v ic2-sandbox-data:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/ic2-sandbox-backup-YYYYMMDD.tar.gz"
```

## Production Deployment

When ready to promote sandbox to production:

1. **Test thoroughly in sandbox**
   - All user management functions
   - Group locking
   - IC2 write operations
   - Data persistence after restarts

2. **Backup production data** (if applicable)

3. **Update production compose file**
   - Copy features from `portainer-ic2-sandbox.yml`
   - Update domain to production URL
   - Enable SSO if needed

4. **Deploy with caution**
   - Consider blue/green deployment
   - Have rollback plan ready
   - Monitor logs closely

## Support & Documentation

- **Sandbox Features**: See `SANDBOX-README.md`
- **GitHub Actions**: `.github/workflows/docker-publish.yml`
- **Portainer Config**: `portainer-ic2-sandbox.yml`

## Quick Reference

| Item | Value |
|------|-------|
| Container Name | IC2-Sandbox |
| Domain | ic2-sandbox.144.202.49.82.nip.io |
| Internal Port | 8000 |
| Volume | ic2-sandbox-data |
| Network | sso_sso_network |
| Default User | alex |
| Default Password | hyrox |
| SSO | Disabled |
| Image Tag | sandbox |
| Registry | ghcr.io |

## Next Steps

After successful deployment:

1. ✅ Test all new features
2. ✅ Create additional test users
3. ✅ Lock/unlock test groups
4. ✅ Verify data persists after container restart
5. ✅ Document any issues or improvements
6. ✅ Plan production rollout
