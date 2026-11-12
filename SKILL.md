---
name: theo-doi-usage
description: Theo dõi usage (hạn mức) của Claude Code ngay trên thanh trạng thái và nhắc một dòng mỗi lượt — % 5 giờ, % 7 ngày (số thật từ rate_limits), % tuần đã trôi, đèn nhịp tuần XANH/VÀNG/ĐỎ/DƯ, và phần Fable (tỷ lệ Fable trong lượng dùng tuần, % Fable ước từ một mốc /usage, hoặc khóa riêng theo model nếu Claude Code gửi). Dùng khi nói "usage", "hạn mức", "còn bao nhiêu %", "đã dùng bao nhiêu % tuần", "Fable dùng bao nhiêu", "cài thanh trạng thái usage", "ghi mốc /usage". Không dùng để đổi gói, mua thêm dung lượng hay đọc nội dung hội thoại. / Track Claude Code usage limits on the status line plus a per-turn reminder: 5-hour %, 7-day %, week elapsed %, pace light (GREEN/YELLOW/RED/SPARE), and the Fable share. Use when asked about "usage", "rate limit", "how much of my week is left", "how much Fable have I used", "install the usage status line", "log a /usage marker".
---

# Theo dõi usage / Usage tracker

## 1. Làm gì (VI)
Thanh trạng thái hiện một dòng, thứ tự cố định:

`Usage 5h 23% | Fable 17% tong | 7d usage 56% | 7d time 48% | VANG`

- `5h` / `7d usage`: % đã dùng, số thật Claude Code gửi cho thanh trạng thái (`rate_limits.five_hour`, `rate_limits.seven_day`). Thiếu cửa sổ nào hiện `-`.
- `7d time`: % tuần đã trôi = 1 − (`seven_day.resets_at` − bây giờ) / 7 ngày. Giờ đặt lại tuần lấy từ `resets_at`, không cứng giờ nào.
- Đèn so `7d usage` với `7d time`: lệch > +10 điểm hoặc ≥ 95% = ĐỎ (`DO`), > +3 = VÀNG (`VANG`), < −8 = DƯ (`DU`), còn lại XANH.
- `Fable`: (a) `Fable 17%` nếu Claude Code gửi khóa hạn mức riêng có chữ "fable"; (b) `Fable ~17%` ước từ mốc `/usage` bạn ghi; (c) `Fable 17% tong` = tỷ lệ Fable trong lượng dùng tuần, tính từ transcript. Không có lượt Fable thì không hiện ô này.
- Hook `UserPromptSubmit` thêm một dòng nhắc mỗi lượt (kèm gợi ý giảm tải khi đèn VÀNG/ĐỎ hoặc 5h ≥ 75%).

## 2. Khi người dùng hỏi (các bước)
1. Hỏi "còn bao nhiêu %" / "Fable dùng bao nhiêu": chạy `python3 <thư mục skill>/scripts/nhip_tuan.py` (hoặc bản đã cài ở `<cấu hình>/usage-tracker/bin/`), đọc kết quả cho người dùng bằng lời thường. Chưa có số: bảo người dùng cài (mục 3) rồi gửi một tin nhắn để thanh trạng thái ghi số.
2. Người dùng muốn % Fable sát hơn: bảo mở `/usage`, đọc hai số "tuần (mọi model)" và "tuần Fable", rồi chạy `nhip_tuan.py --moc <tuần%> <fable%>`.
3. Chưa cài: chạy `python3 <thư mục skill>/install.py --dry-run`, cho người dùng xem, rồi `install.py` khi họ đồng ý.

## 3. Cài / gỡ
`python3 install.py` sao lưu `settings.json`, chép script vào `<cấu hình>/usage-tracker/bin/`, thêm `statusLine` (nếu chưa có) và một nhóm hook `UserPromptSubmit`. Đã có thanh trạng thái khác: không ghi đè, in hướng dẫn nối (`statusline_usage.py --quiet`). Gỡ: `python3 install.py --uninstall`. Chi tiết ở `README.md`.

## 4. Điểm dừng
- Không sửa `settings.json` bằng tay hay lệnh khác ngoài `install.py` (đã sao lưu, hỏi trước khi đụng cái đang có).
- Không ghi đè thanh trạng thái hay hook sẵn có của người dùng. Muốn thay hẳn: để người dùng tự sửa.
- Không xóa thư mục cấu hình; gỡ chỉ xóa đúng mục và tệp skill đã tạo.

## 5. Quyền riêng tư
Chỉ đọc từ transcript ba trường `model`, `usage`, `timestamp` — không đọc nội dung hội thoại. Không gọi mạng. Dữ liệu nằm ở `<cấu hình>/usage-tracker/`; `<cấu hình>` = `CLAUDE_CONFIG_DIR` hoặc `~/.claude`.

## 6. Giới hạn đã biết
- "Quy đổi" tokens (vào mới ×1, ghi cache ×1,25, đọc cache ×0,1, output ×5) là ước lượng, không phải công thức của nhà cung cấp; tỷ lệ Fable và % Fable ước có thể lệch.
- Khóa hạn mức riêng theo model chỉ hiện nếu bản Claude Code của bạn gửi; skill nhận khóa nào có chữ "fable".
- Ngôn ngữ dòng nhắc: `USAGE_TRACKER_LANG=en` (mặc định `vi`).

---

## English
**What it does.** A one-line status bar `Usage 5h 23% | Fable 17% tong | 7d usage 56% | 7d time 48% | YELLOW` (labels `tong` and `VANG` are Vietnamese; with `USAGE_TRACKER_LANG=en` they become `of total` and `YELLOW`) plus a one-line `UserPromptSubmit` reminder each turn. `5h` and `7d usage` are the real numbers Claude Code passes to the status line (`rate_limits`); `7d time` = share of the 7-day window elapsed, computed from `seven_day.resets_at`; the light compares usage with elapsed time. Fable is shown as a real per-model limit if Claude Code sends one, else an estimate from a `/usage` marker you log, else its share of weekly usage read from transcripts (fields `model`, `usage`, `timestamp` only).

**Steps.** (1) Ask: run `scripts/nhip_tuan.py` and explain the result. (2) Better Fable estimate: read `/usage`, then `nhip_tuan.py --moc <week%> <fable%>`. (3) Not installed: `install.py --dry-run`, show the user, then `install.py`.

**Stop points.** Never overwrite an existing status line or hook; never edit settings except through `install.py` (it backs up first); uninstall removes only what the skill added. No network, no conversation content.
