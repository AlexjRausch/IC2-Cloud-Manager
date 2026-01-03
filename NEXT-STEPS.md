# ✅ CODE SUCCESSFULLY PUSHED TO GITHUB!

Your IC2-Sandbox code is now live on GitHub at:
**https://github.com/AlexjRausch/IC2-Cloud-Manager**

## Current Status

✅ **All application code pushed successfully**
✅ **Branch:** main (updated)
✅ **Commits:** 2 commits pushed

## What's Missing

The GitHub Actions workflow file needs to be added manually because the OAuth token doesn't have the `workflow` scope. This is a one-time setup.

## Next Steps (3 minutes total)

### Step 1: Add GitHub Actions Workflow (2 minutes)

1. **Go to your repository:**
   https://github.com/AlexjRausch/IC2-Cloud-Manager

2. **Create the workflow directory:**
   - Click **Add file** > **Create new file**
   - In the filename box, type: `.github/workflows/docker-publish.yml`
   - GitHub will automatically create the directories

3. **Paste this workflow:**

```yaml
name: Build and Publish Docker Container

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=raw,value=latest
            type=raw,value=sandbox
            type=sha,prefix={{branch}}-
            type=ref,event=branch
            type=ref,event=pr

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

4. **Commit the file:**
   - Commit message: `Add GitHub Actions workflow for Docker builds`
   - Click **Commit new file**

5. **Watch the build:**
   - Go to **Actions** tab
   - You'll see "Build and Publish Docker Container" workflow running
   - Wait ~2-3 minutes for build to complete

### Step 2: Deploy to Portainer (1 minute)

Once the GitHub Actions build completes:

1. **Login to your Portainer**

2. **Create Stack:**
   - Navigate to **Stacks**
   - Click **+ Add stack**
   - Name: `ic2-sandbox`

3. **Paste Compose File:**
   Copy the contents from `portainer-ic2-sandbox.yml` (located in your repo or below):

```yaml
version: '3.8'

services:
  ic2-sandbox:
    image: ghcr.io/alexjrausch/ic2-cloud-manager:sandbox
    container_name: IC2-Sandbox
    environment:
      - PEPLINK_CLIENT_ID=${PEPLINK_CLIENT_ID:-1c7314d2ecc9c04138e5c7f0d1b538c9}
      - PEPLINK_CLIENT_SECRET=${PEPLINK_CLIENT_SECRET:-75fb1e2a82fa9ef06380a760d8b96b0e}
      - PEPLINK_API_URL=${PEPLINK_API_URL:-https://api.ic.peplink.com}
      - PORT=8000
      - SSO_ENABLED=false
      - PEPLINK_USERS=${PEPLINK_USERS:-}

    restart: unless-stopped

    volumes:
      - ic2-sandbox-data:/app

    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ic2-sandbox-http.rule=Host(`ic2-sandbox.144.202.49.82.nip.io`)"
      - "traefik.http.routers.ic2-sandbox-http.entrypoints=web"
      - "traefik.http.routers.ic2-sandbox-http.middlewares=https-redirect"
      - "traefik.http.routers.ic2-sandbox.rule=Host(`ic2-sandbox.144.202.49.82.nip.io`)"
      - "traefik.http.routers.ic2-sandbox.entrypoints=websecure"
      - "traefik.http.routers.ic2-sandbox.tls=true"
      - "traefik.http.services.ic2-sandbox.loadbalancer.server.port=8000"
      - "com.centurylinklabs.watchtower.enable=true"

    networks:
      - sso_sso_network

networks:
  sso_sso_network:
    external: true

volumes:
  ic2-sandbox-data:
    driver: local
```

4. **Deploy:**
   - Click **Deploy the stack**
   - Wait for container to start (~30 seconds)

### Step 3: Test Your Sandbox! 🎉

1. **Access the application:**
   ```
   https://ic2-sandbox.144.202.49.82.nip.io
   ```

2. **Login:**
   - Username: `alex`
   - Password: `hyrox`

3. **Test new features:**
   - ✅ Notice "READ-ONLY MODE" badge is gone
   - ✅ Click "Users" button in top banner
   - ✅ Try adding a new user
   - ✅ Click lock icons (🔓) next to groups
   - ✅ Test locking/unlocking groups

## Verification Checklist

After deployment, verify:

- [ ] Container `IC2-Sandbox` is running in Portainer
- [ ] Health check shows as ✅ Healthy
- [ ] Can access https://ic2-sandbox.144.202.49.82.nip.io
- [ ] Can login with alex/hyrox
- [ ] "Users" button appears in header
- [ ] Can open user management modal
- [ ] Lock icons appear next to groups
- [ ] Groups can be locked/unlocked

## Container Details

| Setting | Value |
|---------|-------|
| **Container Name** | IC2-Sandbox |
| **Image** | ghcr.io/alexjrausch/ic2-cloud-manager:sandbox |
| **URL** | https://ic2-sandbox.144.202.49.82.nip.io |
| **Port** | 8000 (internal) |
| **Volume** | ic2-sandbox-data |
| **Network** | sso_sso_network |
| **SSO** | Disabled |

## Features Enabled

🔓 **Write Operations**
- Full IC2 API write access (POST/PUT/DELETE)
- No more read-only restrictions

🔐 **User Management**
- Encrypted password storage (Fernet)
- Add/delete users
- Change passwords
- Role-based access

🔒 **Group Locking**
- Lock groups to prevent changes
- Visual lock indicators
- Persistent across restarts

## Troubleshooting

**Container won't start?**
```bash
docker logs IC2-Sandbox
```

**Can't access URL?**
- Check Traefik is running
- Verify DNS resolves: `nslookup ic2-sandbox.144.202.49.82.nip.io`

**Login fails?**
- Default credentials: alex / hyrox
- Check container logs for errors

**Lost encryption key?**
```bash
# This resets all encrypted data
docker exec IC2-Sandbox rm /app/.encryption_key /app/.users_db.json
docker restart IC2-Sandbox
```

## GitHub Repository

Your code is now at:
**https://github.com/AlexjRausch/IC2-Cloud-Manager**

View commits:
**https://github.com/AlexjRausch/IC2-Cloud-Manager/commits/main**

## Support Documentation

All documentation is in your repository:
- **DEPLOYMENT-GUIDE.md** - Full deployment walkthrough
- **SANDBOX-README.md** - Feature documentation
- **PUSH-INSTRUCTIONS.md** - OAuth workaround details

---

🎉 **You're almost done! Just add the workflow file and deploy to Portainer!**
