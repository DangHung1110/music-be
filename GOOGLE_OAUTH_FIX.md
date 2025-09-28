# Hướng dẫn khắc phục lỗi Google OAuth

## Vấn đề hiện tại
Lỗi "Failed to fetch user info from Google" xảy ra khi đăng nhập bằng Google OAuth.

## Nguyên nhân đã xác định từ logs

### 1. CSRF State Mismatch
- **Lỗi**: `mismatching_state: CSRF Warning! State not equal in request and response`
- **Nguyên nhân**: AuthLib không tự động xử lý state parameter
- **Đã khắc phục**: Thêm manual state generation và verification

### 2. URL Protocol Error
- **Lỗi**: `Request URL is missing an 'http://' or 'https://' protocol`
- **Nguyên nhân**: AuthLib không tìm thấy base URL cho userinfo endpoint
- **Đã khắc phục**: Sử dụng httpx trực tiếp với full URL

### 3. Embedded Null Byte
- **Lỗi**: `ValueError: embedded null byte` trong .env file
- **Nguyên nhân**: File .env có ký tự null byte
- **Cần khắc phục**: Làm sạch file .env

### 4. Cấu hình Google OAuth App
- **Redirect URI không đúng**: Trong Google Cloud Console, redirect URI phải khớp với `GOOGLE_CALLBACK_URL` trong file `.env`
- **Scope không đủ**: App phải có quyền truy cập `openid`, `email`, `profile`
- **Client ID/Secret không đúng**: Kiểm tra lại thông tin trong Google Cloud Console

## Các bước khắc phục

### Bước 1: Kiểm tra Google Cloud Console
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Chọn project của bạn
3. Vào **APIs & Services** > **Credentials**
4. Chọn OAuth 2.0 Client ID
5. Kiểm tra:
   - **Authorized redirect URIs** phải có: `http://localhost:8000/api/v1/auth/google/callback`
   - **Authorized JavaScript origins** phải có: `http://localhost:8000`
   - **Scopes** phải có: `openid`, `email`, `profile`

### Bước 2: Kiểm tra file .env
Đảm bảo các biến sau được cấu hình đúng:
```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_CALLBACK_URL=http://localhost:8000/api/v1/auth/google/callback
FRONTEND_URL=http://localhost:5173
```

### Bước 3: Kiểm tra backend server
1. Khởi động server: `python main.py`
2. Kiểm tra endpoint: `http://localhost:8000/api/v1/auth/google`
3. Kiểm tra logs để xem lỗi chi tiết

### Bước 4: Test OAuth flow
1. Truy cập: `http://localhost:8000/api/v1/auth/google`
2. Đăng nhập Google
3. Kiểm tra callback URL có được gọi không
4. Xem logs để debug

## Code đã được cải thiện

### 1. Thêm debug logging
- Log token nhận được từ Google
- Log profile data
- Log lỗi chi tiết

### 2. Cải thiện error handling
- Xử lý lỗi tốt hơn
- Redirect về frontend với thông báo lỗi
- Fallback từ ID token sang userinfo endpoint

### 3. Cấu hình OAuth tốt hơn
- Thêm userinfo endpoint
- Cải thiện callback URL handling

## Cách test

### 1. Chạy script test
```bash
python test_oauth.py
```

### 2. Test manual
1. Khởi động server
2. Truy cập: `http://localhost:8000/api/v1/auth/google`
3. Đăng nhập Google
4. Kiểm tra logs và kết quả

## Troubleshooting

### Nếu vẫn lỗi:
1. Kiểm tra logs chi tiết
2. Kiểm tra Google Cloud Console
3. Kiểm tra network connectivity
4. Thử với OAuth playground của Google

### Logs quan trọng:
- "Token received: ..."
- "Profile from ID token: ..." hoặc "Profile from userinfo: ..."
- "Google OAuth callback error: ..."

## Lưu ý quan trọng
- Trong production, phải sử dụng HTTPS
- Redirect URI phải khớp chính xác
- Client ID/Secret phải đúng
- CORS phải được cấu hình đúng
