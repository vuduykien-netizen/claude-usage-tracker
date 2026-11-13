"""lang_vi.py - Vietnamese message tables (the `vi` locale, selected with USAGE_TRACKER_LANG=vi).

This is the only source file that contains Vietnamese text. The English tables live next to the
code that prints them (hook_usage.py, nhip_tuan.py, usage_chung.py); every key here matches the
key of the English table of the same name.
"""

# Reminder line printed by hook_usage.py on every prompt.
HOOK = {
    "none": "usage: chưa có số (thanh trạng thái chưa ghi lần nào)",
    "ago": "số cách {m} phút", "old": " (CŨ)", "time": "tuần đã trôi {t}%", "reset": "reset {g}",
    "r5": "5h ≥90%: nên chốt việc đang làm, không mở việc mới",
    "r5b": "5h ≥75%: dùng model nhẹ, gom việc",
    "r7": "7d ≥95%: chỉ việc gấp",
    "Y": "7d đi nhanh hơn lịch: giảm việc song song, dùng model nhẹ",
    "R": "7d vượt lịch nhiều: chỉ việc có hạn",
    "S": "7d còn dư: có thể xả việc xếp hàng",
    "light": "đèn", "fable": "Fable", "tong": "{r}% lượng dùng tuần",
}

# Report printed by nhip_tuan.py.
NHIP = {
    "tuan": "Tuần từ {a} · đã qua {gio:.0f}/168 giờ = {tg:.0f}% thời gian ({nguon})",
    "that": "Đã dùng {u:.0f}% (số thật từ thanh trạng thái, cách {tuoi} phút) · lệch {l:+.0f} điểm · đèn {den}",
    "uoc": "Ước đã dùng {u:.0f}% (từ mốc {luc} = {m:.0f}% + quy đổi phát sinh) · lệch {l:+.0f} điểm · đèn {den}",
    "none": "Chưa có số tuần: cài thanh trạng thái (install.py) hoặc ghi mốc: nhip_tuan.py --moc <tuần%> [fable%]",
    "fthat": "Fable: {p:.0f}% (hạn mức riêng theo model do Claude Code gửi)",
    "fuoc": "Fable: ước {p:.0f}% tuần Fable (mốc {luc} = {m:.0f}%) · quy đổi {q:,.0f} nghìn, {r:.0f}% tổng",
    "fty": "Fable: {q:,.0f} nghìn quy đổi = {r:.0f}% lượng dùng tuần; chưa có mốc % Fable (đọc /usage rồi: nhip_tuan.py --moc <tuần%> <fable%>)",
    "fkhong": "Fable: tuần này chưa thấy lượt dùng model Fable trong transcript",
    "moc": "Đã ghi mốc",
    "sai": "Số phải trong 0..100",
    "est": "ước theo giờ máy, chưa có resets_at",
    "rl": "theo seven_day.resets_at",
}

# Pace-light labels (used by hook_usage.py and nhip_tuan.py).
NHAN_DEN = {"G": "XANH", "Y": "VÀNG", "R": "ĐỎ", "S": "DƯ"}
