# RA2 / Yuri's Revenge — Map Manager

> Phiên bản mới nhất: **v2.1**

Công cụ giao diện đồ họa (GUI) viết bằng Python giúp quản lý, chuẩn hóa định dạng đuôi và đánh số thứ tự hàng loạt cho các file bản đồ của game **Command & Conquer: Red Alert 2 / Yuri's Revenge** (`.map`, `.yrm`, `.mpr`).

---

## ✨ Tính năng chính

- **Quét & Thống kê thư mục thông minh:**
  - Tự động phân loại tổng số map theo 3 định dạng `.map`, `.yrm`, `.mpr`.
  - Tách bạch rõ số lượng **Map đã được cấp số**, **Map chưa được cấp số**, phát hiện các **số bị trùng lặp** và tính toán chính xác **Số lượng map cần cấp mới**.
- **Chuyển đổi định dạng đuôi hàng loạt:**
  - Hỗ trợ chuyển đổi đồng bộ toàn bộ file bản đồ trong thư mục sang một định dạng duy nhất (`.map`, `.yrm` hoặc `.mpr`).
- **Tự động phát hiện & xử lý map trùng số:**
  - Khi phát hiện nhiều map có cùng số thứ tự ở đầu tên file, công cụ tự động giữ nguyên số cho file cũ hơn (dựa theo thời gian chỉnh sửa) và đưa các file trùng vào danh sách chờ cấp số mới.
- **Xử lý dãy số bị khuyết linh hoạt (2 phương án):**
  - Tự động nhận diện các khoảng trống trong dãy số thứ tự hiện có và cung cấp ví dụ minh họa trực quan theo thời gian thực:
    - **Cách 1 — Dồn lại số cho liền mạch & xếp map mới ở cuối:** Lùi số thứ tự của các map cũ để khép kín dãy số, sau đó đánh số nối tiếp cho các map mới ở cuối danh sách.
    - **Cách 2 — Giữ nguyên số cũ & lấp chỗ trống cho map mới:** Giữ nguyên vị trí các map đã có số và ưu tiên điền map mới vào các số thứ tự đang bị trống.
- **Bảng xem trước kết quả (Live Preview):**
  - Mở cửa sổ đối chiếu 3 cột (*Tên file hiện tại – Tên file sau khi đổi – Phân loại*) được phân màu trực quan theo từng nhóm thay đổi trước khi áp dụng lên ổ cứng.
- **Đổi tên 2 bước an toàn (Two-Phase Rename):**
  - Sử dụng tên file tạm gắn mã định danh duy nhất (`UUID`) trong quá trình xử lý, loại bỏ hoàn toàn nguy cơ xung đột hoặc ghi đè file khi lùi số hàng loạt.
- **Giao diện Modern Dark Mode:**
  - Thiết kế nền tối đồng bộ cả thanh tiêu đề Windows, tự động co giãn kích thước cửa sổ theo nội dung hiển thị.

---

## 🚀 Cách sử dụng

### Cách 1: Chạy trực tiếp file thực thi (`.exe`) — Khuyên dùng cho người dùng Windows
1. Truy cập mục **[Releases](../../releases)** ở cột bên phải của repository.
2. Tìm bản phát hành có nhãn **Latest (v2.1)** và tải về file `RA2-Map-Manager-v2.1.exe`.
3. Mở file `.exe`, chọn thư mục chứa map của game, tùy chỉnh định dạng đuôi / phương án đánh số và bấm **BẮT ĐẦU ĐÁNH SỐ & CHUYỂN ĐỔI**.

### Cách 2: Chạy từ mã nguồn Python
**Yêu cầu:** Python 3.8 trở lên (sử dụng thư viện chuẩn `tkinter`, không cần cài thêm thư viện bên ngoài).

```bash
git clone [https://github.com/Khoa-25/rename-maps-RA2.git](https://github.com/Khoa-25/rename-maps-RA2.git)
cd rename-maps-RA2
python rename_maps.py
