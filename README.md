# 🏥 Hệ thống Đặt lịch Khám bệnh

## 📌 Giới thiệu

Ứng dụng hỗ trợ quản lý việc đặt lịch khám bệnh giữa **bệnh nhân – bác sĩ – admin**.  
Người dùng có thể **đặt lịch, thanh toán trực tuyến bằng PayPal, quản lý hồ sơ cá nhân**, trong khi bác sĩ có thể quản lý lịch khám, kê đơn thuốc và theo dõi doanh thu. Admin quản lý toàn bộ hệ thống.

---

## ⚙️ Các chức năng chính

### 👩‍⚕️ Bệnh nhân (Patient)

- Đăng ký, đăng nhập, quản lý hồ sơ cá nhân (họ tên, số điện thoại, email, mật khẩu, avatar).
- Đặt lịch khám với bác sĩ theo khung giờ có sẵn.
- Thanh toán chi phí khám qua **PayPal**:
  - Sau khi đặt lịch → trạng thái **pending**.
  - Thanh toán thành công → trạng thái **completed**.
  - Thanh toán thất bại → lịch hẹn sẽ bị hủy.
- Xem danh sách lịch hẹn và chi tiết cuộc hẹn.

---

### 🩺 Bác sĩ (Doctor)

- Cập nhật thông tin cá nhân (họ tên, chuyên môn, giá khám, avatar).
- Quản lý lịch hẹn của bản thân:
  - Xem danh sách lịch hẹn.
  - Thay đổi trạng thái lịch (pending, completed, cancelled).
- Quản lý bệnh nhân:
  - Xem danh sách bệnh nhân đã đặt lịch với mình.
  - Kê đơn thuốc cho từng bệnh nhân.
- Thống kê:
  - Số lượng lịch hẹn.
  - Doanh thu từ các lịch khám đã hoàn thành.

---

### 👨‍💼 Admin

- Quản lý danh sách **bệnh nhân và bác sĩ**:
- Quản lý lịch hẹn:
  - Xem tất cả lịch hẹn trong hệ thống.
  - Thay đổi trạng thái lịch hẹn (pending, completed, cancelled).
- Quản lý lịch làm việc của bác sĩ:
  - Chọn ngày làm việc

---

## 💳 Thanh toán

- Tích hợp PayPal (sandbox/production).
- Quy trình:
  1. Bệnh nhân đặt lịch → lưu trạng thái **pending**.
  2. Redirect sang PayPal để thanh toán.
  3. Thành công → cập nhật lịch thành **completed**.
  4. Thất bại → xóa lịch hẹn.

---

## 📊 Thống kê

- Bác sĩ có thể xem:
  - Tổng số lịch hẹn đã hoàn thành.
  - Tổng doanh thu (theo ngày, tuần, tháng).
- Admin có thể xem tổng quan toàn hệ thống.

---

## 🚀 Công nghệ sử dụng

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Database**: MySQL
- **Authentication**: Django Auth (Custom User Model)
- **Payment**: PayPal SDK
- **Template engine**: Django Template Language (DTL)

---

## 📌 Hướng phát triển

- Tích hợp thanh toán qua VNPay/Momo.
- Thêm tính năng gửi email/SMS nhắc lịch hẹn.
- Chat trực tiếp giữa bệnh nhân và bác sĩ.
- Thêm API cho mobile app.
