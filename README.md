# 🚀 Bot Đăng Bài Hàng Loạt Telegram

Bot đăng bài lên nhiều kênh Telegram cùng lúc với giao diện đẹp và nhiều tính năng mạnh mẽ.

## ✨ Tính năng chính

- 📢 **Đăng bài hàng loạt**: Gửi bài đến nhiều kênh cùng lúc
- 📋 **Quản lý kênh**: Thêm, xóa, kiểm tra trạng thái kênh
- ⏰ **Lên lịch đăng bài**: Tự động đăng bài theo thời gian
- 🎛️ **Giao diện admin**: Bảng điều khiển với nút inline đẹp mắt
- 📊 **Thống kê chi tiết**: Theo dõi hiệu quả đăng bài
- 🎨 **Đa dạng nội dung**: Hỗ trợ text, hình ảnh, video, file
- 🔄 **Lặp lại tự động**: Đăng bài định kỳ hàng ngày/tuần/tháng
- 💾 **Lưu trữ dữ liệu**: Backup tự động và xuất báo cáo
- 🎨 **Xử lý emoji**: Sửa lỗi emoji Desktop, shortcode, picker

## 🚀 Cài đặt

### 1. Tạo Bot Telegram

1. Truy cập [@BotFather](https://t.me/BotFather) trên Telegram
2. Gửi `/newbot` và làm theo hướng dẫn
3. Lưu token bot được cấp

### 2. Cài đặt phụ thuộc

```bash
pip install -r requirements.txt
```

### 3. Cấu hình Bot

Tạo file `.env` trong thư mục gốc:

```env
# Bot Token từ @BotFather
BOT_TOKEN=your_bot_token_here

# ID của các admin (cách nhau bởi dấu phẩy)
ADMIN_IDS=123456789,987654321

# Số cảnh báo tối đa (mặc định 3)
MAX_WARNINGS=3

# Thời gian mute mặc định (phút)
DEFAULT_MUTE_TIME=60
```

**Cách lấy User ID:**
1. Gửi tin nhắn cho [@userinfobot](https://t.me/userinfobot)
2. Bot sẽ trả về ID của bạn

### 4. Chạy Bot

```bash
python mass_post_bot.py
```

hoặc

```bash
python run.py
```

## 📁 Cấu trúc dự án

```
kf/
├── mass_post_bot.py      # Bot chính với giao diện admin
├── channel_manager.py    # Quản lý kênh Telegram
├── post_manager.py       # Quản lý bài đăng và gửi hàng loạt
├── scheduler.py          # Lên lịch đăng bài tự động
├── emoji_handler.py      # Xử lý emoji và sửa lỗi Desktop
├── config.py             # Cấu hình bot
├── database.py           # Quản lý dữ liệu
├── run.py                # File chạy bot
├── emoji_demo.py         # Demo và test emoji
├── requirements.txt      # Thư viện Python
├── env_example.txt       # Mẫu cấu hình môi trường
└── README.md             # Hướng dẫn này
```

## 📱 Sử dụng

### Lệnh dành cho Admin

| Lệnh | Mô tả | Cách dùng |
|------|-------|-----------|
| `/admin` | Bảng điều khiển admin | `/admin` |
| `/addchannel` | Thêm kênh mới | `/addchannel @channel_username` |
| `/channels` | Danh sách kênh | `/channels` |
| `/post` | Đăng bài ngay | `/post` |
| `/schedule` | Lên lịch đăng bài | `/schedule` |
| `/stats` | Thống kê đăng bài | `/stats` |
| `/cancel` | Hủy thao tác | `/cancel` |
| `/emoji` | Emoji picker | `/emoji` |
| `/emoji_help` | Hướng dẫn emoji | `/emoji_help` |

### Quy trình đăng bài

1. **Thêm kênh**: `/addchannel @your_channel`
2. **Tạo bài đăng**: `/post`
3. **Gửi nội dung**: Text, hình ảnh, video hoặc file
4. **Chọn kênh**: Chọn kênh để đăng
5. **Xác nhận**: Bot sẽ đăng bài tự động

### Lên lịch đăng bài

1. **Tạo lịch**: `/schedule`
2. **Chọn nội dung**: Gửi bài đăng
3. **Chọn thời gian**: Đặt thời gian đăng
4. **Chọn lặp lại**: Hàng ngày/tuần/tháng (tùy chọn)
5. **Xác nhận**: Bot sẽ đăng theo lịch

### 🎨 Xử lý emoji (Khắc phục lỗi Desktop)

**Vấn đề Telegram Desktop:**
- Emoji hiển thị thành `�` hoặc `□`
- Emoji phức hợp bị tách rời
- Emoji không hiển thị đúng khi đăng bài

**Giải pháp của Bot:**
1. **Tự động sửa lỗi**: Bot detect và sửa emoji bị lỗi
2. **Shortcode**: Dùng `[fire]` → 🔥, `[rocket]` → 🚀
3. **Emoji picker**: `/emoji` để chọn emoji từ menu
4. **Gợi ý thông minh**: Bot tự gợi ý emoji phù hợp

**Shortcode phổ biến:**
- `[fire]` → 🔥, `[rocket]` → 🚀, `[star]` → ⭐
- `[heart]` → ❤️, `[money]` → 💰, `[new]` → 🆕
- `[ok]` → ✅, `[no]` → ❌, `[warning]` → ⚠️

## 🎛️ Giao diện Admin

Bot có giao diện admin đẹp mắt với các nút:

- **📢 Đăng bài ngay**: Tạo và đăng bài instantly
- **⏰ Lên lịch đăng**: Đặt thời gian đăng tự động
- **📋 Quản lý kênh**: Thêm, xóa, kiểm tra kênh
- **📊 Thống kê**: Thống kê chi tiết hiệu quả đăng bài
- **📝 Lịch sử đăng**: Xem lịch sử bài đăng
- **⚙️ Cài đặt**: Cấu hình bot và tùy chỉnh

## 🛡️ Bảo mật

- Chỉ admin được cấu hình mới có thể sử dụng bot
- Bot tự động kiểm tra quyền admin trong kênh
- Hệ thống rate limiting tránh spam
- Backup dữ liệu tự động để tránh mất mát

## 🔧 Tùy chỉnh

### Thay đổi delay giữa các lần đăng

Sửa file `.env`:

```env
DEFAULT_DELAY_BETWEEN_POSTS=5  # 5 giây giữa mỗi lần đăng
```

### Cấu hình số kênh tối đa

```env
MAX_CHANNELS_PER_POST=100  # Tối đa 100 kênh mỗi lần đăng
```

### Thay đổi tin nhắn hệ thống

Sửa `WELCOME_MESSAGE` trong `config.py`

### Cấu hình file types được hỗ trợ

Sửa `SUPPORTED_FILE_TYPES` trong `config.py`

## 🐛 Khắc phục sự cố

### Bot không hoạt động
- Kiểm tra token bot có đúng không
- Đảm bảo bot đã được thêm vào kênh với quyền admin

### Không thể đăng bài
- Bot cần có quyền admin trong kênh
- Kiểm tra kênh có tồn tại và hoạt động không

### Lỗi khi thêm kênh
```
❌ Bot không có quyền admin trong kênh này
```
- Thêm bot vào kênh với quyền admin
- Cấp quyền "Post Messages" cho bot

### Lỗi emoji từ Telegram Desktop
```
❌ Emoji hiển thị thành � hoặc □
```
- **Giải pháp 1**: Dùng shortcode `[fire]` thay vì emoji
- **Giải pháp 2**: Dùng `/emoji` để chọn từ picker
- **Giải pháp 3**: Copy emoji từ mobile/web
- **Giải pháp 4**: Bot tự động sửa lỗi khi đăng

### Lỗi khi cài đặt
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 📝 Lưu ý

- Bot cần quyền admin trong kênh để đăng bài
- Backup dữ liệu thường xuyên
- Kiểm tra log để theo dõi hoạt động
- Tránh đăng bài quá nhanh để tránh bị giới hạn API
- Test emoji trước khi đăng hàng loạt: `python emoji_demo.py`

## 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng:

1. Fork repository
2. Tạo branch mới
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📄 License

MIT License - xem file LICENSE để biết chi tiết

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
- Tạo issue trên GitHub
- Liên hệ admin bot
- Kiểm tra log lỗi

---

## 🎯 Tại sao giải pháp này hiệu quả?

**✅ Tự động sửa lỗi emoji Desktop:**
- Bot detect emoji bị lỗi (`�`, `□`) và thay thế
- Ghép lại emoji compound bị tách (👨‍💻)
- Xử lý Unicode escape sequences

**✅ Shortcode system:**
- `[fire]` → 🔥 luôn hoạt động
- Không phụ thuộc vào platform
- Dễ nhớ và nhập nhanh

**✅ Emoji picker tích hợp:**
- Chọn emoji từ menu bot
- Phân loại theo chủ đề
- Gợi ý thông minh dựa trên nội dung

**✅ Validation và optimization:**
- Kiểm tra emoji trước khi đăng
- Cảnh báo nếu quá nhiều emoji
- Tối ưu hiệu suất đăng bài

**🆚 So với các giải pháp khác:**
- **Copy từ mobile** → Bất tiện, cần chuyển device
- **Dùng web Telegram** → Chậm, không tiện cho đăng hàng loạt
- **Gõ mã Unicode** → Khó nhớ, dễ lỗi
- **Bot này** → Tự động, nhanh, chính xác, tích hợp sẵn

**Chúc bạn đăng bài hiệu quả! 🚀** 