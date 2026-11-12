# theo-doi-usage

Skill cho Claude Code: xem usage (hạn mức) ngay trên thanh trạng thái, kèm đèn nhịp tuần và phần Fable. Python 3 chuẩn, không thư viện ngoài, chạy trên Windows / macOS / Linux. MIT.

*English summary below.*

```
Usage 5h 23% | Fable 17% tong | 7d usage 56% | 7d time 48% | VANG
```

| Ô | Nghĩa |
|---|---|
| `5h` | % hạn mức 5 giờ đã dùng (số thật của Claude Code) |
| `Fable` | `17%` khóa riêng của model · `~17%` ước từ mốc `/usage` · `17% tong` tỷ lệ Fable trong lượng dùng tuần (từ transcript) |
| `7d usage` | % hạn mức 7 ngày đã dùng (số thật) |
| `7d time` | % tuần đã trôi, từ `seven_day.resets_at` |
| đèn | `XANH` đúng nhịp · `VANG` nhanh hơn lịch · `DO` vượt lịch nhiều · `DU` còn dư |

Mỗi lượt gõ, hook `UserPromptSubmit` thêm một dòng nhắc cùng số liệu. Chỉ hiện sau khi Claude Code gửi `rate_limits` (gói đăng nhập có hạn mức; sau tin nhắn đầu tiên).

## Cài (3 bước)

1. Đặt thư mục này vào `~/.claude/skills/theo-doi-usage/` (hoặc `$CLAUDE_CONFIG_DIR/skills/theo-doi-usage/`).
2. Xem trước: `python3 ~/.claude/skills/theo-doi-usage/install.py --dry-run`
3. Cài: `python3 ~/.claude/skills/theo-doi-usage/install.py`, rồi mở lại Claude Code.

`install.py`: sao lưu `settings.json` (`settings.json.usage-tracker.<giờ>.bak`), chép script vào `<cấu hình>/usage-tracker/bin/`, thêm `statusLine` nếu bạn chưa có, thêm một nhóm hook `UserPromptSubmit` (giữ nguyên hook sẵn có), giữ mọi khóa khác. Đã có thanh trạng thái riêng thì **không ghi đè**: nó in lệnh để bạn nối, ví dụ trong script của bạn chuyển JSON stdin cho `statusline_usage.py --quiet` (chỉ ghi số, không in).
Windows: dùng `py -3` hoặc `python` thay `python3` nếu cần. `<cấu hình>` = `CLAUDE_CONFIG_DIR`, mặc định `~/.claude`.

## Ghi mốc để % Fable sát hơn (tùy chọn)

Mở `/usage`, đọc "tuần (mọi model)" và "tuần Fable", rồi:
`python3 ~/.claude/skills/theo-doi-usage/scripts/nhip_tuan.py --moc 73 47`
(`--luc "2026-01-15 13:05"` nếu đọc số lúc khác). Chạy `nhip_tuan.py` không đối số để xem nhịp tuần chi tiết. `USAGE_TRACKER_LANG=en` đổi dòng nhắc sang tiếng Anh.

## Gỡ bỏ an toàn

`python3 ~/.claude/skills/theo-doi-usage/install.py --uninstall` (thêm `--dry-run` để xem trước) chỉ:
- bỏ `statusLine` **nếu chính skill đặt**, bỏ đúng hook skill thêm (hook và khóa khác của bạn giữ nguyên), sao lưu `settings.json` trước;
- xóa đúng 4 tệp script trong `<cấu hình>/usage-tracker/bin/` do skill chép.

Không đụng thư mục cấu hình. Số liệu `<cấu hình>/usage-tracker/` (`rate.json`, `moc.jsonl`, `nhip-cache.json`) được giữ; xóa tay thư mục `usage-tracker` nếu không cần nữa.
Nếu bạn đã tự nối `statusline_usage.py --quiet` vào script của mình, hãy gỡ dòng đó tay.

## Quyền riêng tư

Chỉ đọc ba trường `model`, `usage`, `timestamp` trong transcript (`<cấu hình>/projects/**/*.jsonl`); không đọc nội dung hội thoại, không gọi mạng, không đọc thông tin đăng nhập.

## Kiểm thử

`python3 tests/kiem_thu.py` (dùng thư mục tạm, không đụng cấu hình thật); `--pha` đặt kỳ vọng sai có ý để chắc bộ kiểm bắt được.

## Tệp

`SKILL.md` · `install.py` · `scripts/statusline_usage.py` · `scripts/hook_usage.py` · `scripts/nhip_tuan.py` · `scripts/usage_chung.py` · `tests/kiem_thu.py` · `LICENSE`

---

## English

A Claude Code skill that puts your usage limits on the status line: real 5-hour and 7-day percentages (from `rate_limits`), the share of the week elapsed (from `seven_day.resets_at`), a pace light (`XANH`/`VANG`/`DO`/`DU` = green/yellow/red/spare; `USAGE_TRACKER_LANG=en` prints `GREEN`/`YELLOW`/`RED`/`SPARE` in the reminder), and Fable: a real per-model limit if Claude Code sends one, an estimate from a `/usage` marker, or its share of weekly usage from transcripts. A `UserPromptSubmit` hook adds a one-line reminder each turn. Python 3 standard library only.

**Install.** (1) Put this folder at `~/.claude/skills/theo-doi-usage/`. (2) `python3 install.py --dry-run`. (3) `python3 install.py`, then restart Claude Code. It backs up `settings.json`, never overwrites an existing status line (prints how to chain `statusline_usage.py --quiet` instead), adds one hook group and keeps your other hooks and keys.

**Log a marker (optional).** Read `/usage`, then `python3 scripts/nhip_tuan.py --moc <week%> <fable%>`.

**Uninstall.** `python3 install.py --uninstall` removes only the entries and the four script files it added; your config directory, other hooks and settings stay. Data in `<config>/usage-tracker/` is kept.

**Privacy.** Reads only `model`, `usage`, `timestamp` from transcripts; no conversation content, no network.

**Caveats.** Weighted-token conversion (input ×1, cache write ×1.25, cache read ×0.1, output ×5) is an estimate; the Fable share and the Fable estimate can be off. A per-model limit key appears only if your Claude Code version sends one.
