# TiniX Story 1.0 - Hướng dẫn sử dụng toàn tập

Chào mừng bạn đến với **TiniX Story 1.0**, hệ thống AI hỗ trợ sáng tác tiểu thuyết và nội dung dài kỳ cấp chuyên nghiệp. Tài liệu này sẽ hướng dẫn bạn chi tiết từ cách cài đặt, cấu hình ban đầu cho đến cách tận dụng tối đa các tính năng của phần mềm.

---

## 📦 1. Bắt đầu nhanh & Cài đặt

### Yêu cầu hệ thống
- Hệ điều hành: Windows 10/11, macOS, hoặc Linux.
- Python: Phiên bản 3.8 trở lên (Khuyến nghị 3.11).

### Cài đặt và Khởi động
Nếu bạn đã tải mã nguồn về máy:

1. **Tạo và kích hoạt môi trường ảo (Virtual Environment):**
   ```bash
   python -m venv venv
   
   # Kích hoạt trên Windows:
   venv\Scripts\activate
   
   # Kích hoạt trên Mac/Linux:
   source venv/bin/activate
   ```

2. **Cài đặt thư viện phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```
   *Lưu ý: Nếu bạn muốn upload và xử lý file PDF hoặc EPUB, hãy cài thêm các thư viện hỗ trợ:*
   ```bash
   pip install PyMuPDF ebooklib beautifulsoup4
   ```

3. **Khởi động ứng dụng:**
   ```bash
   python app.py
   ```
   Sau khi màn hình console báo thành công, hãy mở trình duyệt và truy cập vào đường link được hiển thị (thường là `http://127.0.0.1:7860`).

---

## ⚙️ 2. Cấu hình Hệ thống & API (Bước quan trọng đầu tiên)

Trước khi bắt đầu sáng tác, bạn **bắt buộc** phải cấu hình API để AI có thể hoạt động.

1. Chuyển sang thẻ **⚙️ Cài đặt hệ thống**.
2. Tại tab **🌐 Quản lý giao diện (Interface Management)**, tiến hành thêm cấu hình API mới:
   - **Tên giao diện:** Đặt tên bất kỳ (Ví dụ: `My OpenAI`, `Gemini Pro`).
   - **Loại giao diện:** Chọn nhà cung cấp phù hợp (OpenAI, Anthropic, v.v.). Nếu dùng API tương thích OpenAI, hãy điền đúng Base URL.
   - **Tên mô hình:** Nhập chính xác mã mô hình (VD: `gpt-4o`, `claude-3-5-sonnet-20240620`, `gemini-1.5-pro`).
   - **API Key:** Nhập mã khóa bí mật của bạn (Sẽ không được lưu dưới dạng văn bản thuần túy).
   - Hãy tích chọn **Sử dụng làm mặc định** nếu đây là API chính của bạn.
3. Nhấp **➕ Thêm giao diện**. Hệ thống sẽ thông báo thành công.
4. Chuyển qua tab **📝 Tham số tạo** để tinh chỉnh:
   - **Temperature (Độ sáng tạo):** Mặc định 0.7. Mức cao (>0.8) cho văn phong sáng tạo, bay bổng. Mức thấp (<0.5) cho văn phong logic, nhất quán.
   - **Mục tiêu chữ mỗi chương:** Thiết lập số chữ bạn mong muốn cho một chương (Mặc định thường là 1500 - 2000 chữ).

---

## ✍️ 3. Các tính năng sáng tác cốt lõi

### 3.1. Sáng tác từ con số không (Create from Scratch)
Chức năng này dành cho việc xây dựng một bộ tiểu thuyết hoàn toàn mới.
- Điền các thông tin cơ bản: Tên tiểu thuyết, Thể loại, Chủ đề phụ.
- Nhấp **✨ Nhận cảm hứng trí tuệ nhân tạo** để gợi ý Tên sách, Tuyến nhân vật, Thế giới quan.
- Sau khi có đủ Thiết lập, nhấp **Tạo dàn ý**. Phải đảm bảo dàn ý tuân thủ cấu trúc mỗi dòng một chương để hệ thống nhận diện đúng.
- Bấm **Bắt đầu tạo / Tiếp tục** để AI bắt đầu viết từng chương. Hệ thống tự động ghi nhớ bối cảnh (context) từ các chương trước.

### 3.2. Chế độ Viết lại (Rewrite Mode)
Chức năng dùng để thay đổi văn phong của một đoạn văn bản có sẵn.
- Tải tệp lên (TXT, DOCX, v.v.) hoặc dán trực tiếp.
- Lựa chọn cách phân đoạn để AI không bị quá tải: Tự động, theo số lượng chữ, hoặc theo biểu thức/cụm từ tùy chỉnh (VD: Phân tách theo "Chương").
- Chọn một trong **17 phong cách văn học** (Tiên hiệp, Lãng mạn đô thị, Kinh dị, Khoa học viễn tưởng, Hardcore...).
- Bấm **Bắt đầu viết lại**. Hệ thống sẽ chạy và bạn có thể theo dõi trực tiếp.

### 3.3. Chế độ Viết tiếp (Continue Mode)
Dành cho trường hợp bạn viết dở hoặc có một tác phẩm đang dang dở.
- Điền các thiết lập nhân vật, thế giới quan (nếu có, để AI nắm bắt tốt hơn).
- Cung cấp nội dung văn bản phần trước.
- AI sẽ phân tích văn phong, giọng văn và tự động viết tiếp cốt truyện một cách logic.

### 3.4. Trau chuốt tiểu thuyết (Novel Polish)
Giống như một biên tập viên chuyên nghiệp rà soát lại tác phẩm của bạn.
- Cung cấp văn bản thô.
- Chọn loại hình trau chuốt: 
  - **Comprehensive:** Trau chuốt toàn diện.
  - **Find Errors:** Tìm lỗi chính tả, ngữ pháp, logic.
  - **Remove AI Tone:** Làm cho câu chữ tự nhiên và "giống người viết" hơn.
  - **Enhance Details:** Phóng to các chi tiết miêu tả cảm quan, bối cảnh.
  - **Optimize Dialogue:** Làm mượt mà và cá nhân hóa lời thoại.

---

## 📂 4. Quản lý Dự án & Xuất file

- **Thẻ Quản lý Dự án:** Mọi dự án bạn tạo (Sáng tác, Viết lại, Viết tiếp) đều được tự động lưu trữ tại đây. Bạn có thể xem **Tiến độ hoàn thành**, số lượng chương. Nếu bạn muốn tạm ngưng, cứ tắt app; sau đó vào đây chọn dự án và bấm **Viết tiếp (Continue)** để khôi phục tiến trình.
- **Thẻ Xuất (Export):** Cho phép bạn xuất dự án hoàn chỉnh ra nhiều định dạng chuyên nghiệp như `.docx` (Word), `.txt`, `.md` hoặc `.html`. Rất tiện lợi để gửi cho tòa soạn hoặc đăng tải lên các nền tảng đọc truyện online.

---

## 🛠 5. Khắc phục sự cố (Troubleshooting)

| Vấn đề | Nguyên nhân & Cách giải quyết |
|--------|------------------------------|
| **Không thể tải (load) API** | Kiểm tra lại kết nối mạng hoặc API Key có chính xác không. Nhấn "Test" trong phần cài đặt Backend để xem lỗi phản hồi từ máy chủ trả về. |
| **API trả về 0 chữ** | Hệ thống TiniX Story sẽ **tự động thử lại** tối đa 3 lần. Nếu vẫn thất bại, hãy giảm "Max Tokens" hoặc kiểm tra lại prompt thiết lập xem có vi phạm chính sách của nhà cung cấp API không. |
| **Lỗi cài thư viện DOCX** | Nếu xuất file Word báo lỗi, hãy chạy thủ công lệnh `pip install python-docx` trên Terminal. |
| **Cổng 7860 bị từ chối** | App sẽ tự tìm một cổng khác (ví dụ 7861, 7862...). Hãy để ý thông báo URL ở Terminal. |
| **Giao diện hiển thị tiếng Anh**| Đảm bảo thiết lập `set APP_LANGUAGE=VI` (Windows cmd) trước khi chạy `python app.py` nếu bạn không muốn thấy giao diện mặc định. |
