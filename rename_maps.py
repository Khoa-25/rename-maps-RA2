import os
import re
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

SOURCE_EXTS = ('.map', '.yrm', '.mpr')
NUM_PATTERN = re.compile(r'^(\d+)\.\s*')

# Bảng màu Modern Dark Mode (Slate + Amber & Emerald)
BG_MAIN, BG_CARD, BG_SUB = "#0F172A", "#1E293B", "#0B1120"
BORDER, INPUT_BORDER = "#334155", "#475569"
PRIMARY, PRIMARY_HOVER = "#2563EB", "#1D4ED8"
AMBER, EMERALD, CYAN = "#FBBF24", "#34D399", "#38BDF8"
HEADER_BG, TEXT, MUTED, ERR = "#020617", "#F8FAFC", "#94A3B8", "#F87171"

unnumbered_count = 0

def font(size=10, bold=True):
    return ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)

def update_range_display(*_):
    if unnumbered_count == 0:
        lbl_will_num.config(text="• Số lượng map sẽ đánh số: 0 map (Không có map mới)", fg=MUTED)
        return
    try:
        start = int(start_var.get())
        if start < 1:
            raise ValueError
        end = start + unnumbered_count - 1
        lbl_will_num.config(
            text=f"• Số lượng map sẽ đánh số: {unnumbered_count} map (từ số {start} đến số {end})",
            fg=EMERALD
        )
    except ValueError:
        lbl_will_num.config(
            text=f"• Số lượng map sẽ đánh số: {unnumbered_count} map (Lỗi số bắt đầu)",
            fg=ERR
        )

def scan_folder(target_dir):
    global unnumbered_count
    if not target_dir or not os.path.isdir(target_dir):
        lbl_total.config(text="• Tổng số map hiện tại (với 3 đuôi: .map, .yrm, .mpr): 0 map", fg=ERR)
        lbl_num.config(text="    ◦ Số lượng map đã đánh số: 0 map", fg=MUTED)
        lbl_range.config(text="        - Chưa có dữ liệu", fg=MUTED)
        lbl_unnum.config(text="    ◦ Số lượng map chưa đánh số: 0 map", fg=MUTED)
        unnumbered_count = 0
        return update_range_display()

    map_files = [f for f in os.listdir(target_dir) if f.lower().endswith(SOURCE_EXTS)]
    nums = [int(m.group(1)) for f in map_files if (m := NUM_PATTERN.match(f))]
    numbered_count = len(nums)
    unnumbered_count = len(map_files) - numbered_count
    max_num = max(nums, default=0)

    lbl_total.config(text=f"• Tổng số map hiện tại (với 3 đuôi: .map, .yrm, .mpr): {len(map_files)} map", fg=TEXT)
    lbl_num.config(text=f"    ◦ Số lượng map đã đánh số: {numbered_count} map", fg="#CBD5E1")
    lbl_range.config(
        text=f"        - Hiện đã đánh từ số {min(nums)} đến số {max_num}" if nums else "        - Chưa có map nào được đánh số",
        fg=MUTED
    )
    lbl_unnum.config(
        text=f"    ◦ Số lượng map chưa đánh số: {unnumbered_count} map",
        fg=AMBER if unnumbered_count else MUTED
    )

    start_var.set(str(max_num + 1))
    update_range_display()

def browse_folder():
    if selected := filedialog.askdirectory():
        folder_var.set(selected)
        scan_folder(selected)

def process_files():
    target_dir, target_ext = folder_var.get(), ext_var.get()
    if not target_dir or not os.path.isdir(target_dir):
        return messagebox.showerror("Thiếu thông tin", "Vui lòng chọn một thư mục hợp lệ!")
    try:
        start_num = int(start_var.get())
        if start_num < 1:
            raise ValueError
    except ValueError:
        return messagebox.showerror("Sai định dạng", "Số bắt đầu phải là một số nguyên lớn hơn 0!")

    curr_num, count, added, errors = start_num, 0, 0, []
    try:
        for fname in sorted(os.listdir(target_dir), key=str.lower):
            if not fname.lower().endswith(SOURCE_EXTS):
                continue
            base, _ = os.path.splitext(fname)
            has_num = bool(NUM_PATTERN.match(fname))
            new_name = (f"{curr_num}.{base}" if not has_num else base) + target_ext
            if new_name == fname:
                continue

            new_path = os.path.join(target_dir, new_name)
            if os.path.exists(new_path):
                errors.append(f"Bỏ qua '{fname}' vì '{new_name}' đã tồn tại.")
                continue

            os.rename(os.path.join(target_dir, fname), new_path)
            count += 1
            if not has_num:
                curr_num += 1
                added += 1

        scan_folder(target_dir)
        msg = f"Hoàn tất! Đã xử lý thành công {count} file."
        if added:
            msg += f"\n• Đã đánh số {added} map mới (từ {start_num} đến {curr_num - 1})."
        if errors:
            extra = f"\n...và {len(errors) - 5} file khác." if len(errors) > 5 else ""
            msg += "\n\nCác file bị bỏ qua do trùng tên:\n" + "\n".join(errors[:5]) + extra
        messagebox.showinfo("Hoàn tất", msg)
    except Exception as e:
        messagebox.showerror("Lỗi hệ thống", f"Đã xảy ra lỗi: {e}")

# --- KHỞI TẠO GIAO DIỆN ---
root = tk.Tk()
root.title("RA2 / Yuri's Revenge - Map Manager")
root.configure(bg=BG_MAIN)
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")
style.layout(
    "Slate.TRadiobutton",
    [("Radiobutton.padding", {"children": [("Radiobutton.indicator", {"side": "left", "sticky": ""}), ("Radiobutton.label", {"sticky": "nswe"})], "sticky": "nswe"})]
)
style.configure("Slate.TRadiobutton", background=BG_CARD, foreground=TEXT, font=font(10, False), indicatorcolor=BG_SUB, indicatordiameter=14, focusthickness=0, focuscolor=BG_CARD, padding=4)
style.map("Slate.TRadiobutton", background=[("active", BG_CARD)], foreground=[("active", "#FFFFFF")], indicatorcolor=[("selected", CYAN), ("active", BORDER)])

folder_var = tk.StringVar()
ext_var = tk.StringVar(value=".map")
start_var = tk.StringVar(value="1")
start_var.trace_add("write", update_range_display)

def make_card(parent):
    c = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
    c.pack(fill="x", pady=(0, 12))
    return c

def make_lbl(parent, text, fg=TEXT, size=10, bold=True, bg=BG_CARD, **pack_kw):
    w = tk.Label(parent, text=text, bg=bg, fg=fg, font=font(size, bold), anchor="w")
    w.pack(**pack_kw)
    return w

def make_entry(parent, var, fg=TEXT, accent=CYAN, width=None, justify="left", **pack_kw):
    e = tk.Entry(parent, textvariable=var, width=width, font=font(10, bold=(width is not None)), justify=justify, bg=BG_SUB, fg=fg, insertbackground="#FFFFFF", relief="flat", highlightthickness=1, highlightbackground=INPUT_BORDER, highlightcolor=accent)
    e.pack(**pack_kw)
    return e

def make_btn(parent, text, cmd, bg, hover, **pack_kw):
    b = tk.Button(parent, text=text, command=cmd, bg=bg, fg="#FFFFFF" if bg == PRIMARY else TEXT, activebackground=hover, activeforeground="#FFFFFF", font=font(10), relief="flat", takefocus=False, cursor="hand2")
    b.pack(**pack_kw)
    b.bind("<Enter>", lambda _: b.config(bg=hover))
    b.bind("<Leave>", lambda _: b.config(bg=bg))
    return b

# Header
header = tk.Frame(root, bg=HEADER_BG, height=54)
header.pack(fill="x")
header.pack_propagate(False)
make_lbl(header, "QUẢN LÝ & ĐỔI TÊN MAP (RA2 / YURI'S REVENGE)", size=11, bg=HEADER_BG, side="left", padx=20)
tk.Frame(root, bg=PRIMARY, height=2).pack(fill="x")

main = tk.Frame(root, bg=BG_MAIN)
main.pack(fill="both", expand=True, padx=18, pady=14)

# Card 1: Thư mục
c1 = make_card(main)
make_lbl(c1, "1. Thư mục chứa file (.map, .yrm, .mpr)", anchor="w", padx=14, pady=(10, 6))
dir_row = tk.Frame(c1, bg=BG_CARD)
dir_row.pack(fill="x", padx=14, pady=(0, 12))
make_entry(dir_row, folder_var, side="left", fill="x", expand=True, ipady=5, padx=(0, 8))
make_btn(dir_row, "Chọn thư mục...", browse_folder, "#334155", "#475569", side="right", padx=12, pady=4)

# Card 2: Thống kê thư mục (giữ nguyên 4 dòng hiện trạng)
c2 = make_card(main)
make_lbl(c2, "Thống kê thư mục", anchor="w", padx=14, pady=(10, 4))
box = tk.Frame(c2, bg=BG_SUB, highlightbackground=BORDER, highlightthickness=1)
box.pack(fill="x", padx=14, pady=(2, 12))
lbl_total = make_lbl(box, "• Tổng số map hiện tại (với 3 đuôi: .map, .yrm, .mpr): Chưa quét thư mục", MUTED, 10, True, BG_SUB, fill="x", padx=10, pady=(6, 2))
lbl_num = make_lbl(box, "    ◦ Số lượng map đã đánh số: --", MUTED, 9, True, BG_SUB, fill="x", padx=10, pady=1)
lbl_range = make_lbl(box, "        - Hiện đã đánh từ số: --", MUTED, 9, False, BG_SUB, fill="x", padx=10, pady=1)
lbl_unnum = make_lbl(box, "    ◦ Số lượng map chưa đánh số: --", MUTED, 9, True, BG_SUB, fill="x", padx=10, pady=(1, 6))

# Card 3: Đuôi file
c3 = make_card(main)
make_lbl(c3, "2. Định dạng đuôi muốn chuyển đổi thành", anchor="w", padx=14, pady=(10, 4))
radio_row = tk.Frame(c3, bg=BG_CARD)
radio_row.pack(anchor="w", padx=14, pady=(0, 10))
for ext in SOURCE_EXTS:
    ttk.Radiobutton(radio_row, text=ext, variable=ext_var, value=ext, style="Slate.TRadiobutton", takefocus=False, cursor="hand2").pack(side="left", padx=(0, 28))

# Card 4: Đánh số thứ tự (chuyển dòng "Số lượng map sẽ đánh số..." xuống đây)
c4 = make_card(main)
make_lbl(c4, "3. Đánh số thứ tự đầu file (ví dụ: 19.european.map)", anchor="w", padx=14, pady=(10, 4))
num_row = tk.Frame(c4, bg=BG_CARD)
num_row.pack(anchor="w", padx=14, pady=(0, 6))
make_lbl(num_row, "Thêm số cho map chưa đánh số, bắt đầu từ:", side="left")
make_entry(num_row, start_var, fg=EMERALD, accent=EMERALD, width=6, justify="center", side="left", padx=8, ipady=2)
lbl_will_num = make_lbl(c4, "• Số lượng map sẽ đánh số: --", MUTED, 10, True, anchor="w", padx=14, pady=(0, 10))

# Nút thực thi
make_btn(main, "BẮT ĐẦU ĐÁNH SỐ & CHUYỂN ĐỔI", process_files, PRIMARY, PRIMARY_HOVER, fill="x", pady=(4, 2), ipady=6)

root.update_idletasks()
root.geometry(f"{max(590, root.winfo_reqwidth())}x{root.winfo_reqheight()}")
root.mainloop()