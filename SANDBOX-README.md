# IC2-Sandbox - Testing Environment

This is the sandbox/testing version of the Peplink InControl2 Manager with full write capabilities enabled.

## What's New in This Version

### 1. Write Operations Enabled
- The application now supports full IC2 API write operations (POST, PUT, DELETE)
- Removed "READ-ONLY MODE" badge from the header
- All IC2 API endpoints can be accessed through `/api/ic2/*` proxy endpoints

### 2. User Management System
- **Encrypted Password Storage**: All passwords are encrypted using Fernet (symmetric encryption)
- **User Management UI**: Access via the "Users" button in the top banner
- **Features**:
  - Add new users with role-based access (user/admin)
  - Change user passwords
  - Delete users (except default admin 'alex')
  - All user data stored in encrypted `.users_db.json` file

### 3. Group Locking Feature
- **Lock Groups**: Prevent accidental changes to specific groups
- **Toggle Lock**: Click the lock icon (🔒/🔓) next to any group in the sidebar
- **Persistent**: Lock status is saved and persists across restarts
- Lock status stored in `.locked_groups.json` file

### 4. Security Enhancements
- Encryption key automatically generated and stored in `.encryption_key`
- All sensitive files have secure permissions (600)
- Session-based authentication maintained

## Deployment Instructions

### Build the Container

```bash
docker compose -f docker-compose-sandbox.yml build
```

### Deploy to Test Environment

```bash
docker compose -f docker-compose-sandbox.yml up -d
```

### Stop the Sandbox

```bash
docker compose -f docker-compose-sandbox.yml down
```

### View Logs

```bash
docker compose -f docker-compose-sandbox.yml logs -f ic2-sandbox
```

## Configuration

The sandbox environment uses the following configuration:

- **Container Name**: IC2-Sandbox
- **Domain**: ic2-sandbox.144.202.49.82.nip.io
- **Port**: 8000 (internal)
- **SSO**: Disabled for testing
- **Default Credentials**: alex / hyrox
- **Data Persistence**: Enabled via Docker volume `ic2-sandbox-data`

## Environment Variables

All environment variables from the production version are supported:

```yaml
PEPLINK_CLIENT_ID       # IC2 API Client ID
PEPLINK_CLIENT_SECRET   # IC2 API Client Secret
PEPLINK_API_URL        # IC2 API URL
PORT                   # Application port (default: 8000)
SSO_ENABLED           # Enable SSO (disabled in sandbox)
PEPLINK_USERS         # Additional users (format: user1:pass1,user2:pass2)
```

## Data Persistence

The following files are persisted in the Docker volume:

1. `.encryption_key` - Fernet encryption key (auto-generated)
2. `.users_db.json` - Encrypted user database
3. `.locked_groups.json` - Group lock status

**IMPORTANT**: Do not delete the `.encryption_key` file or you will lose access to encrypted passwords!

## API Endpoints

### User Management
- `GET /api/users` - List all users (without passwords)
- `POST /api/users` - Add new user
- `PUT /api/users/{username}` - Update user password
- `DELETE /api/users/{username}` - Delete user

### Group Management
- `POST /api/group-lock` - Toggle group lock status
- `GET /api/locked-groups` - Get locked groups list

### IC2 API Proxy
- `GET /api/ic2/*` - Proxy GET requests to IC2
- `POST /api/ic2/*` - Proxy POST requests to IC2
- `PUT /api/ic2/*` - Proxy PUT requests to IC2
- `DELETE /api/ic2/*` - Proxy DELETE requests to IC2

## Security Notes

1. **Encryption**: All passwords are encrypted using Fernet symmetric encryption
2. **Key Security**: The encryption key is stored in `.encryption_key` with 600 permissions
3. **Session Security**: Sessions use HttpOnly and SameSite=Strict cookies
4. **Default Admin**: The 'alex' user cannot be deleted to prevent lockout

## Testing Checklist

Before promoting to production:

- [ ] Test user management (add, update, delete)
- [ ] Test group locking feature
- [ ] Test IC2 write operations
- [ ] Verify encryption is working
- [ ] Check data persistence after container restart
- [ ] Verify all API endpoints
- [ ] Test authentication flow
- [ ] Review logs for errors

## Differences from Production

| Feature | Production | Sandbox |
|---------|-----------|---------|
| SSO | Enabled (Authentik) | Disabled |
| Domain | ic2.144.202.49.82.nip.io | ic2-sandbox.144.202.49.82.nip.io |
| Write Operations | Enabled | Enabled |
| Container Name | peplink-ic2-manager | IC2-Sandbox |
| Volume | None | ic2-sandbox-data |

## Troubleshooting

### Lost Encryption Key
If the encryption key is lost, you'll need to:
1. Stop the container
2. Delete `.encryption_key` and `.users_db.json`
3. Restart the container (will regenerate with default users)

### Cannot Login
1. Check container logs: `docker compose -f docker-compose-sandbox.yml logs ic2-sandbox`
2. Verify credentials (default: alex / hyrox)
3. Try deleting `.users_db.json` to reset to defaults

### Group Lock Not Working
1. Check `.locked_groups.json` exists and has correct permissions
2. Verify API endpoint is responding: `curl http://localhost:8000/api/locked-groups`

## Next Steps

Once testing is complete:
1. Update production docker-compose.yml with new features
2. Backup current production data
3. Deploy to production with appropriate environment variables
4. Monitor for issues
5. Update documentation
