# Peplink InControl2 Manager

A containerized web-based dashboard for monitoring Peplink devices via the InControl2 API.

## Features

- Web-based interface for Peplink device management
- Secure authentication with session management
- Real-time device monitoring via InControl2 API
- Containerized deployment with Docker

## Quick Start with Docker

### Using Docker Compose (Recommended)

1. **Start the application**
   ```bash
   docker-compose up -d
   ```

2. **Access the dashboard**
   - Open http://localhost:8000
   - Default credentials: `alex` / `hyrox`

3. **View logs**
   ```bash
   docker-compose logs -f
   ```

4. **Stop the application**
   ```bash
   docker-compose down
   ```

### Using Docker CLI

1. **Build the image**
   ```bash
   docker build -t peplink-ic2-manager .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name peplink-ic2-manager \
     -p 8000:8000 \
     -e PEPLINK_CLIENT_ID=your_client_id \
     -e PEPLINK_CLIENT_SECRET=your_client_secret \
     peplink-ic2-manager
   ```

3. **Access the dashboard**
   - Open http://localhost:8000

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PEPLINK_CLIENT_ID` | Peplink API Client ID | `1c7314d2ecc9c04138e5c7f0d1b538c9` |
| `PEPLINK_CLIENT_SECRET` | Peplink API Client Secret | `75fb1e2a82fa9ef06380a760d8b96b0e` |
| `PEPLINK_API_URL` | Peplink API Base URL | `https://api.ic.peplink.com` |
| `PORT` | Application port | `8000` |
| `PEPLINK_USERS` | User credentials (format: `user1:pass1,user2:pass2`) | `alex:hyrox` |

### Custom Configuration

Create a `.env` file in the same directory as `docker-compose.yml`:

```env
PEPLINK_CLIENT_ID=your_client_id_here
PEPLINK_CLIENT_SECRET=your_client_secret_here
PEPLINK_API_URL=https://api.ic.peplink.com
PEPLINK_USERS=admin:securepassword,user:password123
```

Then run:
```bash
docker-compose up -d
```

## Deployment to Remote Server

### Deploy to Portainer

1. **Copy files to your server**
   ```bash
   scp -r peplink-clean/ user@your-server:/path/to/deployment/
   ```

2. **In Portainer**
   - Navigate to Stacks → Add Stack
   - Name: `peplink-ic2-manager`
   - Upload `docker-compose.yml` or paste its contents
   - Add environment variables as needed
   - Deploy the stack

### Deploy to your Linux VM (192.168.5.35)

1. **Copy files**
   ```bash
   scp -r peplink-clean/ alexhost2026@192.168.5.35:/home/alexhost2026/
   ```

2. **SSH into the server**
   ```bash
   ssh alexhost2026@192.168.5.35
   ```

3. **Deploy**
   ```bash
   cd ~/peplink-clean
   docker-compose up -d
   ```

4. **Access via Portainer**
   - Navigate to http://portainer.local:9000
   - View and manage the container

## Health Check

The container includes a health check that runs every 30 seconds:
- Endpoint: `/health`
- Returns: `{"status": "ok"}`

Check container health:
```bash
docker ps
# Look for "healthy" status
```

## Security Notes

- Default credentials should be changed in production
- Use strong passwords when setting `PEPLINK_USERS`
- The container runs as a non-root user for security
- Session cookies are HttpOnly and SameSite protected

## Troubleshooting

### View logs
```bash
docker-compose logs -f peplink-manager
```

### Restart the container
```bash
docker-compose restart
```

### Rebuild after code changes
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Check if port 8000 is in use
```bash
lsof -i :8000
# or
netstat -an | grep 8000
```

## API Endpoints

- `GET /` - Main dashboard (requires authentication)
- `GET /login` - Login page
- `POST /login` - Authentication endpoint
- `GET /logout` - Logout endpoint
- `GET /health` - Health check endpoint
- `GET /api/orgs` - Get organizations
- `GET /api/groups/{org_id}` - Get groups for organization
- `GET /api/devices/{org_id}` - Get devices for organization

## License

This is a custom application for Peplink InControl2 device management.
