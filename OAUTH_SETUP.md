# OAuth Setup Guide

## Environment Variables Required

Thêm các biến môi trường sau vào file `.env` hoặc docker-compose.yml:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Facebook OAuth  
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

## Google OAuth Setup

1. Truy cập [Google Cloud Console](https://console.developers.google.com/)
2. Tạo project mới hoặc chọn project hiện có
3. Enable Google+ API
4. Tạo OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/api/v1/auth/google/callback`
5. Copy Client ID và Client Secret

## Facebook OAuth Setup

1. Truy cập [Facebook Developers](https://developers.facebook.com/)
2. Tạo app mới
3. Thêm Facebook Login product
4. Cấu hình Facebook Login:
   - Valid OAuth Redirect URIs: `http://localhost:8000/api/v1/auth/facebook/callback`
5. Copy App ID và App Secret

## API Endpoints

### OAuth Initiation
- `GET /api/v1/auth/google` - Redirect to Google OAuth
- `GET /api/v1/auth/facebook` - Redirect to Facebook OAuth

### OAuth Callbacks
- `GET /api/v1/auth/google/callback` - Handle Google OAuth callback
- `GET /api/v1/auth/facebook/callback` - Handle Facebook OAuth callback

## Frontend Integration

Frontend sẽ nhận redirect với các parameters:
- `access_token` - JWT access token
- `refresh_token` - JWT refresh token  
- `session_id` - Session ID
- `expires_in` - Token expiration time
- `refresh_expires_in` - Refresh token expiration time
- `user_data` - User information

Hoặc nếu có lỗi:
- `error=true` - Error flag
- `message` - Error message

## Database Migration

Chạy migration để thêm OAuth fields:

```bash
alembic upgrade head
```

## Testing

1. Start backend: `docker-compose up`
2. Test Google OAuth: `GET http://localhost:8000/api/v1/auth/google`
3. Test Facebook OAuth: `GET http://localhost:8000/api/v1/auth/facebook`
