# 🌐 Bảng Điều Khiển Web - Bot Đăng Bài Hàng Loạt

## 📋 Tổng quan

Bảng điều khiển web cung cấp giao diện trực quan để quản lý bot đăng bài hàng loạt Telegram một cách dễ dàng thông qua trình duyệt web.

## 🚀 Cách chạy Dashboard

### Phương pháp 1: Chạy trực tiếp
```bash
python start_dashboard.py
```

### Phương pháp 2: Chạy từ file gốc
```bash
python simple_dashboard.py
```

Dashboard sẽ mở tại: **http://localhost:8000**

## 🎯 Các tính năng chính

### 1. 🏠 **Trang chủ Dashboard**
- Thống kê tổng quan về bot
- Số lượng kênh, bài đăng đã lên lịch
- Trạng thái hoạt động của bot
- Liên kết nhanh đến các chức năng

### 2. 📢 **Quản lý kênh**
- Xem danh sách tất cả kênh
- Thêm kênh mới (Channel ID hoặc @username)
- Xóa kênh không cần thiết
- Hiển thị trạng thái kênh

### 3. ✍️ **Đăng bài hàng loạt**
- Soạn nội dung bài đăng
- Toolbar emoji nhanh (🔥🚀⭐❤️👍💰🆕🏷️)
- Chọn nhiều kênh cùng lúc
- Hỗ trợ shortcode emoji: `[fire]` → 🔥

### 4. ⏰ **Lên lịch đăng bài**
- Lên lịch đăng bài tự động
- Lặp lại theo ngày/tuần/tháng
- Quản lý lịch đã tạo
- Hủy lịch đăng bài

### 5. 😊 **Công cụ Emoji**
- Xử lý emoji từ Telegram Desktop
- Chuyển đổi shortcode thành emoji
- Sửa lỗi emoji bị lỗi hiển thị

## 📱 Giao diện

### Responsive Design
- Tương thích tất cả thiết bị
- Giao diện thân thiện với người dùng
- Điều hướng đơn giản

### Màu sắc & Thiết kế
- Giao diện hiện đại, sạch sẽ
- Màu xanh chủ đạo (#2196F3)
- Card design cho thống kê
- Bảng dữ liệu rõ ràng

## 🔧 Cấu hình

### Cổng mạng
- **Mặc định**: 8000
- **URL**: http://localhost:8000
- **Thay đổi**: Sửa trong `start_dashboard.py`

### File dữ liệu
- `channels.json` - Danh sách kênh
- `posts.json` - Lịch sử bài đăng
- `scheduled_posts.json` - Lịch đăng bài

## 🛠️ Yêu cầu hệ thống

### Python Dependencies
```
# Không cần thư viện bên ngoài
# Chỉ sử dụng thư viện chuẩn Python
```

### Trình duyệt hỗ trợ
- Chrome/Chromium
- Firefox
- Safari
- Edge

## 🚦 Hướng dẫn sử dụng

### Bước 1: Khởi động Dashboard
```bash
python start_dashboard.py
```

### Bước 2: Truy cập Dashboard
- Mở trình duyệt
- Vào địa chỉ: http://localhost:8000
- Dashboard sẽ tự động mở

### Bước 3: Quản lý kênh
1. Nhấn **"Quản lý kênh"**
2. Thêm Channel ID hoặc @username
3. Đặt tên hiển thị cho kênh
4. Nhấn **"Thêm kênh"**

### Bước 4: Đăng bài
1. Nhấn **"Đăng bài"**
2. Soạn nội dung bài đăng
3. Sử dụng toolbar emoji
4. Chọn kênh đích
5. Nhấn **"Đăng bài ngay"**

### Bước 5: Lên lịch
1. Nhấn **"Lịch đăng"**
2. Soạn nội dung
3. Chọn thời gian đăng
4. Chọn loại lặp lại
5. Nhấn **"Lên lịch"**

## 📊 Thống kê & Giám sát

### Thông tin hiển thị
- **Tổng số kênh**: Số kênh đã thêm
- **Kênh hoạt động**: Số kênh đang hoạt động
- **Bài đăng đã lên lịch**: Số bài chờ đăng
- **Trạng thái bot**: Tình trạng hoạt động

### Cập nhật real-time
- Thống kê tự động cập nhật
- Refresh trang để xem thay đổi mới nhất

## 🔒 Bảo mật

### Cổng local
- Dashboard chỉ chạy trên localhost
- Không thể truy cập từ mạng ngoài
- An toàn cho môi trường local

### Dữ liệu
- Lưu trữ local trên máy
- Không gửi dữ liệu ra ngoài
- File JSON dễ backup

## 🐛 Xử lý lỗi

### Lỗi phổ biến
1. **Cổng đã được sử dụng**
   - Đổi cổng trong code
   - Hoặc tắt ứng dụng đang dùng cổng 8000

2. **Không mở được browser**
   - Thủ công vào http://localhost:8000
   - Kiểm tra firewall

3. **File không tồn tại**
   - Dashboard tự tạo file cần thiết
   - Kiểm tra quyền ghi file

## 📝 Ghi chú

- Dashboard hoạt động độc lập với bot Telegram
- Có thể chạy song song với bot
- Dữ liệu đồng bộ qua file JSON
- Giao diện demo - một số chức năng cần tích hợp thêm

## 🔄 Tương lai

### Tính năng sẽ thêm
- [ ] Tích hợp trực tiếp với bot Telegram
- [ ] Upload file media
- [ ] Xem trước bài đăng
- [ ] Thống kê chi tiết hơn
- [ ] Backup/restore dữ liệu
- [ ] Multi-user support

---

**🎉 Chúc bạn sử dụng Dashboard hiệu quả!** 