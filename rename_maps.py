import os
import re
import uuid
import ctypes
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

SOURCE_EXTS = ('.map', '.yrm', '.mpr')
NUM_PATTERN = re.compile(r'^(\d+)\.\s*(.*)$')

# Bảng màu Modern Dark Mode
BG_MAIN, BG_CARD, BG_SUB = "#0F172A", "#1E293B", "#0B1120"
BORDER, INPUT_BORDER = "#334155", "#475569"
PRIMARY, PRIMARY_HOVER = "#2563EB", "#1D4ED8"
AMBER, EMERALD, CYAN = "#FBBF24", "#34D399", "#38BDF8"
HEADER_BG, TEXT, MUTED, ERR = "#020617", "#F8FAFC", "#94A3B8", "#F87171"
DESC_TEXT = "#CBD5E1"

unnumbered_count = 0
numbered_stats = {"count": 0, "min": 0, "max": 0, "used": set()}
missing_nums_global = []
preview_plan_cache = []

def font(size=10, bold=True):
    return ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)

def apply_dark_titlebar(window):
    """Chuyển thanh tiêu đề mặc định của Windows sang chế độ nền tối (Dark Mode)."""
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
        value = ctypes.c_int(2)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        if res != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        pass

def resize_window():
    root.update_idletasks()
    root.geometry(f"{max(680, root.winfo_reqwidth())}x{root.winfo_reqheight()}")

def short_fname(name, max_len=22):
    """Rút gọn tên file quá dài nhưng vẫn giữ phần số đầu và đuôi file."""
    if len(name) <= max_len:
        return name
    base, ext = os.path.splitext(name)
    keep = max_len - len(ext) - 1
    return f"{base[:max(8, keep)]}…{ext}"

def short_stem(name, max_len=16):
    """Lấy tên file không kèm phần mở rộng và rút gọn nếu quá dài."""
    base, _ = os.path.splitext(name)
    if len(base) <= max_len:
        return base
    return f"{base[:max(8, max_len - 1)]}…"

def build_sample_segments(items, limit=3):
    """Tạo danh sách đoạn văn bản hiển thị các ví dụ đầu (in đậm số thứ tự) và không có dấu phẩy trước +N."""
    if not items:
        return []
    segments = []
    for idx, (_, new, _) in enumerate(items[:limit]):
        if idx > 0:
            segments.append((", ", None))
        s_name = short_fname(new, 21)
        if "." in s_name:
            num_part, rest_part = s_name.split(".", 1)
            segments.append((num_part, "bold"))
            segments.append((f".{rest_part}", None))
        else:
            segments.append((s_name, None))
    if len(items) > limit:
        segments.append((f" +{len(items) - limit} file khác", None))
    return segments

def set_rich_desc(txt_widget, segments):
    """Cập nhật nội dung cho dòng mô tả lựa chọn."""
    txt_widget.config(state="normal")
    txt_widget.delete("1.0", "end")
    for text, tag in segments:
        if tag:
            txt_widget.insert("end", text, tag)
        else:
            txt_widget.insert("end", text)
    txt_widget.config(state="disabled")

def classify_maps(target_dir):
    """Phân loại map hợp lệ, map chưa cấp số và tách riêng các map bị trùng số."""
    map_files = [f for f in os.listdir(target_dir) if f.lower().endswith(SOURCE_EXTS)]
    grouped_by_num = defaultdict(list)
    unnumbered_items = []

    for fname in map_files:
        base, _ = os.path.splitext(fname)
        full_path = os.path.join(target_dir, fname)
        try:
            mtime = os.path.getmtime(full_path)
        except OSError:
            mtime = 0

        if m := NUM_PATTERN.match(base):
            num = int(m.group(1))
            clean_name = m.group(2).strip() or base
            grouped_by_num[num].append((mtime, fname.lower(), num, clean_name, fname))
        else:
            unnumbered_items.append((base, fname, False))

    numbered_items = []
    duplicate_nums = []
    dup_reassigned_count = 0

    for num in sorted(grouped_by_num.keys()):
        entries = sorted(grouped_by_num[num], key=lambda x: (x[0], x[1]))
        _, _, n, clean_name, fname = entries[0]
        numbered_items.append((n, clean_name, fname))

        if len(entries) > 1:
            duplicate_nums.append(num)
            for _, _, _, dup_clean, dup_fname in entries[1:]:
                unnumbered_items.append((dup_clean, dup_fname, True))
                dup_reassigned_count += 1

    unnumbered_items.sort(key=lambda x: x[1].lower())
    return len(map_files), numbered_items, unnumbered_items, duplicate_nums, dup_reassigned_count

def compute_rename_plan(target_dir, target_ext, start_num, mode):
    """Tính toán trước danh sách đổi tên cho chế độ bất kỳ để dùng chung cho Preview & Thực thi."""
    if not target_dir or not os.path.isdir(target_dir):
        return []

    _, numbered_items, unnumbered_items, _, _ = classify_maps(target_dir)
    nums = [item[0] for item in numbered_items]
    missing_nums = sorted(set(range(min(nums), max(nums) + 1)) - set(nums)) if nums else []

    plan = []
    if mode == "compact":
        curr_num = numbered_items[0][0] if numbered_items else start_num
        for old_num, clean_name, fname in numbered_items:
            new_name = f"{curr_num}.{clean_name}{target_ext}"
            if new_name != fname:
                tag = "Đôn số" if curr_num != old_num else "Đổi đuôi"
                plan.append((fname, new_name, tag))
            curr_num += 1

        curr_num = max(curr_num, start_num)
        for base, fname, is_dup in unnumbered_items:
            new_name = f"{curr_num}.{base}{target_ext}"
            plan.append((fname, new_name, "Trùng số → Mới" if is_dup else "Map mới"))
            curr_num += 1
    else:
        used_nums = set()
        for old_num, clean_name, fname in numbered_items:
            used_nums.add(old_num)
            new_name = f"{old_num}.{clean_name}{target_ext}"
            if new_name != fname:
                plan.append((fname, new_name, "Đổi đuôi"))

        gap_pool = list(missing_nums)
        curr_num = start_num
        for base, fname, is_dup in unnumbered_items:
            if gap_pool:
                num_to_use = gap_pool.pop(0)
                tag = "Lấp số khuyết"
            else:
                while curr_num in used_nums:
                    curr_num += 1
                num_to_use = curr_num
                curr_num += 1
                tag = "Trùng số → Mới" if is_dup else "Map mới"
            used_nums.add(num_to_use)
            plan.append((fname, f"{num_to_use}.{base}{target_ext}", tag))

    return plan

def on_gap_mode_change(*_):
    if not missing_nums_global:
        return
    if gap_mode_var.get() == "compact":
        start_var.set(str(numbered_stats["min"] + numbered_stats["count"]))
    else:
        start_var.set(str(numbered_stats["max"] + 1))
    update_range_display()

def update_preview_button(plan):
    was_mapped = preview_wrap.winfo_ismapped()
    if plan:
        btn_preview.config(text=f"👁  Xem trước kết quả sau khi đổi ({len(plan)} file)")
        if not was_mapped:
            preview_wrap.pack(fill="x", pady=(2, 8), before=btn_run)
            resize_window()
    elif was_mapped:
        preview_wrap.pack_forget()
        resize_window()

def update_range_display(*_):
    global preview_plan_cache
    target_dir = folder_var.get()
    target_ext = ext_var.get()
    mode = gap_mode_var.get() if missing_nums_global else "fill"

    try:
        start = int(start_var.get())
        if start < 1:
            raise ValueError
        valid_start = True
    except ValueError:
        start = numbered_stats["max"] + 1
        valid_start = False

    if not target_dir or not os.path.isdir(target_dir):
        preview_plan_cache = []
        lbl_will_num.config(text="• Số lượng map sẽ cấp số: --", fg=MUTED)
        update_preview_button([])
        return

    active_plan = compute_rename_plan(target_dir, target_ext, start, mode) if valid_start else []
    preview_plan_cache = active_plan

    if missing_nums_global:
        missing_str = ", ".join(map(str, missing_nums_global[:6])) + ("..." if len(missing_nums_global) > 6 else "")

        # --- Ví dụ thực tế Cách 1 (lùi số + 2 ví dụ map mới) ---
        base_c_start = numbered_stats["min"] + numbered_stats["count"]
        c_start = max(base_c_start, start) if (mode == "compact" and valid_start) else base_c_start
        plan_c = active_plan if mode == "compact" else compute_rename_plan(target_dir, target_ext, c_start, "compact")

        shifted_c = [x for x in plan_c if x[2] == "Đôn số"]
        new_c = [x for x in plan_c if x[2] in ("Map mới", "Trùng số → Mới")]

        opt1_segments = []
        if shifted_c:
            old_nums = [int(x[0].split(".", 1)[0]) for x in shifted_c]
            new_nums = [int(x[1].split(".", 1)[0]) for x in shifted_c]
            old_range_str = f"{old_nums[0]}–{old_nums[-1]}" if len(old_nums) > 1 else f"{old_nums[0]}"
            new_range_str = f"{new_nums[0]}–{new_nums[-1]}" if len(new_nums) > 1 else f"{new_nums[0]}"
            old_ex = short_stem(shifted_c[0][0], 16)
            new_ex = short_stem(shifted_c[0][1], 16)

            opt1_segments.extend([
                (f"• Map cũ: Lùi số của {len(shifted_c)} file từ {old_range_str} xuống {new_range_str} (VD: {old_ex} ", None),
                ("→", "amber"),
                (f" {new_ex})\n", None),
            ])
        else:
            opt1_segments.append(("• Map cũ: Không cần lùi số\n", None))

        if new_c:
            opt1_segments.append((f"• Map mới ({len(new_c)} file): ", None))
            opt1_segments.extend(build_sample_segments(new_c, 2))
        else:
            opt1_segments.append(("• Map mới: Không có", None))

        set_rich_desc(txt_opt1_desc, opt1_segments)

        # --- Ví dụ thực tế Cách 2 (3 ví dụ map mới) ---
        f_start = start if (mode == "fill" and valid_start) else numbered_stats["max"] + 1
        plan_f = active_plan if mode == "fill" else compute_rename_plan(target_dir, target_ext, f_start, "fill")
        new_f = [x for x in plan_f if x[2] in ("Lấp số khuyết", "Map mới", "Trùng số → Mới")]

        old_range = (
            f"từ số {numbered_stats['min']} đến {numbered_stats['max']}"
            if numbered_stats["min"] != numbered_stats["max"]
            else f"số {numbered_stats['min']}"
        )
        opt2_segments = [(f"• Map cũ: Giữ nguyên vị trí {old_range}\n", None)]
        if new_f:
            opt2_segments.append((f"• Map mới ({len(new_f)} file): ", None))
            opt2_segments.extend(build_sample_segments(new_f, 3))
        else:
            opt2_segments.append((f"• Map mới: Không có (số khuyết {missing_str} vẫn để trống)", None))

        set_rich_desc(txt_opt2_desc, opt2_segments)

        # --- Dòng xác nhận chế độ đang chọn ---
        if not valid_start:
            lbl_will_num.config(text="• Lỗi: Số bắt đầu phải là số nguyên lớn hơn 0", fg=ERR)
            update_preview_button([])
            return

        mode_label = "Cách 1 — Dồn số liền mạch" if mode == "compact" else "Cách 2 — Giữ số cũ & lấp chỗ trống"
        if active_plan:
            lbl_will_num.config(text=f"• Đã chọn: {mode_label} ({len(active_plan)} file sẽ cập nhật)", fg=EMERALD)
        else:
            lbl_will_num.config(text=f"• Đã chọn: {mode_label} (Không có file nào thay đổi)", fg=MUTED)
        update_preview_button(active_plan)
        return

    # --- Trường hợp thư mục không bị khuyết số ---
    if not valid_start:
        lbl_will_num.config(text=f"• Số lượng map sẽ cấp số: {unnumbered_count} map (Lỗi số bắt đầu)", fg=ERR)
        update_preview_button([])
    elif active_plan:
        if unnumbered_count > 0:
            end = start + unnumbered_count - 1
            lbl_will_num.config(
                text=f"• Số lượng map sẽ cấp số: {unnumbered_count} map (từ số {start} đến số {end})",
                fg=EMERALD
            )
        else:
            lbl_will_num.config(
                text=f"• Cập nhật định dạng đuôi cho {len(active_plan)} map sang {target_ext}",
                fg=EMERALD
            )
        update_preview_button(active_plan)
    else:
        lbl_will_num.config(text="• Số lượng map sẽ cấp số: 0 map (Không có thay đổi)", fg=MUTED)
        update_preview_button([])

def open_preview_window():
    """Mở bảng đối chiếu 3 cột chi tiết có phân màu theo từng nhóm thay đổi."""
    if not preview_plan_cache:
        return

    win = tk.Toplevel(root)
    win.title(f"Dự đoán kết quả sau khi đổi ({len(preview_plan_cache)} file)")
    win.configure(bg=BG_MAIN)
    win.geometry("840x460")
    win.minsize(680, 340)
    win.transient(root)
    win.grab_set()
    apply_dark_titlebar(win)

    top = tk.Frame(win, bg=HEADER_BG, height=44)
    top.pack(fill="x")
    top.pack_propagate(False)
    tk.Label(
        top,
        text=f"DỰ ĐOÁN KẾT QUẢ SAU KHI ĐỔI ({len(preview_plan_cache)} FILE SẼ CẬP NHẬT)",
        bg=HEADER_BG, fg=TEXT, font=font(10)
    ).pack(side="left", padx=16)

    legend = tk.Frame(top, bg=HEADER_BG)
    legend.pack(side="right", padx=16)
    tk.Label(legend, text="● Lùi / Đôn số", bg=HEADER_BG, fg=AMBER, font=font(8, True)).pack(side="left", padx=(0, 10))
    tk.Label(legend, text="● Map mới / Lấp khuyết", bg=HEADER_BG, fg=EMERALD, font=font(8, True)).pack(side="left", padx=(0, 10))
    tk.Label(legend, text="● Đổi đuôi", bg=HEADER_BG, fg="#CBD5E1", font=font(8, False)).pack(side="left")

    tk.Frame(win, bg=CYAN, height=2).pack(fill="x")

    style.configure(
        "Dark.Treeview",
        background=BG_SUB,
        foreground=TEXT,
        fieldbackground=BG_SUB,
        rowheight=26,
        font=font(9, False),
        borderwidth=0
    )
    style.configure(
        "Dark.Treeview.Heading",
        background=BG_CARD,
        foreground=CYAN,
        font=font(9, True),
        relief="flat"
    )

    def fixed_map(option):
        return [elm for elm in style.map("Dark.Treeview", query_opt=option) if elm[:2] != ("!disabled", "!selected")]

    style.map(
        "Dark.Treeview",
        foreground=fixed_map("foreground"),
        background=[("selected", PRIMARY)] + fixed_map("background")
    )

    table_wrap = tk.Frame(win, bg=BG_MAIN)
    table_wrap.pack(fill="both", expand=True, padx=14, pady=12)

    cols = ("old", "new", "type")
    tree = ttk.Treeview(table_wrap, columns=cols, show="headings", style="Dark.Treeview")
    tree.heading("old", text="Tên file hiện tại")
    tree.heading("new", text="Tên file sau khi đổi")
    tree.heading("type", text="Phân loại")

    tree.column("old", width=348, anchor="w")
    tree.column("new", width=348, anchor="w")
    tree.column("type", width=115, anchor="center", stretch=False)

    tree.tag_configure("shift", foreground=AMBER)
    tree.tag_configure("new", foreground=EMERALD)
    tree.tag_configure("ext", foreground="#CBD5E1")

    scrollbar = ttk.Scrollbar(table_wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    for old_n, new_n, tag_type in preview_plan_cache:
        if tag_type == "Đôn số":
            row_tag = "shift"
        elif tag_type in ("Map mới", "Lấp số khuyết", "Trùng số → Mới"):
            row_tag = "new"
        else:
            row_tag = "ext"
        tree.insert("", "end", values=(old_n, new_n, tag_type), tags=(row_tag,))

    bottom = tk.Frame(win, bg=BG_MAIN)
    bottom.pack(fill="x", padx=14, pady=(0, 12))
    tk.Label(
        bottom,
        text="Kiểm tra kỹ cột 'Tên file sau khi đổi' trước khi bấm thực thi ở màn hình chính.",
        bg=BG_MAIN, fg=MUTED, font=font(8, False)
    ).pack(side="left")
    make_btn(bottom, "Đóng", win.destroy, "#334155", "#475569", side="right", padx=16, pady=3)

    win.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - win.winfo_width()) // 2
    y = root.winfo_y() + (root.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{max(0, x)}+{max(0, y)}")
    win.after(10, lambda: apply_dark_titlebar(win))

def scan_folder(target_dir):
    global unnumbered_count, missing_nums_global, numbered_stats
    if not target_dir or not os.path.isdir(target_dir):
        lbl_total.config(text="• Tổng số map (.map, .yrm, .mpr): 0", fg=ERR)
        lbl_num.config(text="    ◦ Map đã được cấp số: 0", fg=MUTED)
        lbl_invalid_num.pack_forget()
        lbl_unnum.config(text="    ◦ Map chưa được cấp số: 0", fg=MUTED)
        lbl_unnum.pack_configure(pady=(1, 6))
        lbl_need_num.pack_forget()
        lbl_dup_note.pack_forget()
        unnumbered_count, missing_nums_global = 0, []
        numbered_stats = {"count": 0, "min": 0, "max": 0, "used": set()}
        gap_box.pack_forget()
        update_range_display()
        return resize_window()

    total_files, numbered_items, unnumbered_items, duplicate_nums, dup_count = classify_maps(target_dir)
    nums = [item[0] for item in numbered_items]
    numbered_count = len(nums)
    unnumbered_count = len(unnumbered_items)
    max_num = max(nums, default=0)
    min_num = min(nums, default=0)
    numbered_stats = {"count": numbered_count, "min": min_num, "max": max_num, "used": set(nums)}

    # Số lượng thực tế các file đang có số vs chưa có số trong thư mục
    actual_numbered_count = numbered_count + dup_count
    actual_unnumbered_count = unnumbered_count - dup_count

    lbl_total.config(text=f"• Tổng số map (.map, .yrm, .mpr): {total_files}", fg=TEXT)

    if nums:
        missing_nums_global = sorted(set(range(min_num, max_num + 1)) - set(nums))
        if missing_nums_global:
            preview_missing = ", ".join(map(str, missing_nums_global[:8])) + (", ..." if len(missing_nums_global) > 8 else "")
            lbl_gap_title.config(text=f"⚠ Số thứ tự bị trống: {preview_missing} — Hãy chọn cách xử lý:")
            if not gap_box.winfo_ismapped():
                gap_box.pack(fill="x", padx=14, pady=(4, 8), before=lbl_will_num)
        else:
            gap_box.pack_forget()

        lbl_num.config(
            text=f"    ◦ Map đã được cấp số: {actual_numbered_count}",
            fg=DESC_TEXT
        )

        if duplicate_nums:
            preview_dup = ", ".join(map(str, duplicate_nums[:8])) + (", ..." if len(duplicate_nums) > 8 else "")
            lbl_invalid_num.config(
                text=f"        - Số được cấp không hợp lệ: {preview_dup} (bị trùng số)",
                fg=AMBER
            )
            if not lbl_invalid_num.winfo_ismapped():
                lbl_invalid_num.pack(fill="x", padx=10, pady=1, before=lbl_unnum)
        else:
            lbl_invalid_num.pack_forget()
    else:
        missing_nums_global = []
        lbl_num.config(text="    ◦ Map đã được cấp số: 0", fg=MUTED)
        lbl_invalid_num.pack_forget()
        gap_box.pack_forget()

    if dup_count:
        lbl_unnum.config(
            text=f"    ◦ Map chưa được cấp số: {actual_unnumbered_count}",
            fg=DESC_TEXT if actual_unnumbered_count else MUTED
        )
        lbl_unnum.pack_configure(pady=1)

        if actual_unnumbered_count > 0:
            detail_txt = f"({actual_unnumbered_count} chưa được cấp số + {dup_count} bị trùng số)"
        else:
            detail_txt = f"({dup_count} bị trùng số)"

        lbl_need_num.config(text=f"• Số lượng map cần cấp mới: {unnumbered_count} {detail_txt}", fg=AMBER)
        lbl_dup_note.config(
            text="    • Số map được cấp cũ hơn sẽ được giữ nguyên và số bị trùng sẽ được cấp mới"
        )
        if not lbl_need_num.winfo_ismapped():
            lbl_need_num.pack(fill="x", padx=10, pady=(4, 1))
        if not lbl_dup_note.winfo_ismapped():
            lbl_dup_note.pack(fill="x", padx=10, pady=(0, 6))
    else:
        lbl_unnum.config(
            text=f"    ◦ Map chưa được cấp số: {actual_unnumbered_count}",
            fg=AMBER if actual_unnumbered_count else MUTED
        )
        lbl_unnum.pack_configure(pady=(1, 6))
        lbl_need_num.pack_forget()
        lbl_dup_note.pack_forget()

    if missing_nums_global and gap_mode_var.get() == "compact":
        start_var.set(str(min_num + numbered_count))
    else:
        start_var.set(str(max_num + 1))

    update_range_display()
    resize_window()

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

    scan_folder(target_dir)
    mode = gap_mode_var.get() if missing_nums_global else "fill"
    plan = compute_rename_plan(target_dir, target_ext, start_num, mode)

    if not plan:
        return messagebox.showinfo("Thông báo", "Tất cả file trong thư mục đều đã đúng định dạng và số thứ tự!")

    sources = {old for old, _, _ in plan}
    valid_renames = []
    errors = []
    seen_targets = set()

    for old_name, new_name, tag_type in plan:
        new_path = os.path.join(target_dir, new_name)
        if new_name in seen_targets or (os.path.exists(new_path) and new_name not in sources):
            errors.append(f"Bỏ qua '{old_name}' vì '{new_name}' đã tồn tại.")
            continue
        seen_targets.add(new_name)
        valid_renames.append((old_name, new_name, tag_type))

    try:
        temp_map = []
        for old_name, new_name, _ in valid_renames:
            tmp_name = f".__tmp_{uuid.uuid4().hex}_{old_name}"
            os.rename(os.path.join(target_dir, old_name), os.path.join(target_dir, tmp_name))
            temp_map.append((tmp_name, new_name))

        for tmp_name, new_name in temp_map:
            os.rename(os.path.join(target_dir, tmp_name), os.path.join(target_dir, new_name))

        scan_folder(target_dir)
        shifted_cnt = sum(1 for _, _, t in valid_renames if t == "Đôn số")
        new_logs = [f"{old} → {new}" for old, new, t in valid_renames if t in ("Map mới", "Lấp số khuyết", "Trùng số → Mới")]

        msg = f"Hoàn tất! Đã xử lý thành công {len(valid_renames)} file."
        if shifted_cnt:
            msg += f"\n• Đã lùi số thứ tự cho {shifted_cnt} map cũ."
        if new_logs:
            msg += f"\n• Đã cấp số cho {len(new_logs)} map mới:\n    - " + "\n    - ".join(new_logs[:6])
            if len(new_logs) > 6:
                msg += f"\n    ...và {len(new_logs) - 6} map khác."
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
radio_layout = [("Radiobutton.padding", {"children": [("Radiobutton.indicator", {"side": "left", "sticky": ""}), ("Radiobutton.label", {"sticky": "nswe"})], "sticky": "nswe"})]

style.layout("Slate.TRadiobutton", radio_layout)
style.configure("Slate.TRadiobutton", background=BG_CARD, foreground=TEXT, font=font(10, False), indicatorcolor=BG_SUB, indicatordiameter=14, focusthickness=0, focuscolor=BG_CARD, padding=4)
style.map("Slate.TRadiobutton", background=[("active", BG_CARD)], foreground=[("active", "#FFFFFF")], indicatorcolor=[("selected", CYAN), ("active", BORDER)])

style.layout("Sub.TRadiobutton", radio_layout)
style.configure("Sub.TRadiobutton", background=BG_SUB, foreground=TEXT, font=font(9, True), indicatorcolor=BG_CARD, indicatordiameter=13, focusthickness=0, focuscolor=BG_SUB, padding=2)
style.map("Sub.TRadiobutton", background=[("active", BG_SUB)], foreground=[("active", EMERALD)], indicatorcolor=[("selected", AMBER), ("active", BORDER)])

folder_var = tk.StringVar()
ext_var = tk.StringVar(value=".map")
start_var = tk.StringVar(value="1")
gap_mode_var = tk.StringVar(value="compact")

start_var.trace_add("write", update_range_display)
ext_var.trace_add("write", update_range_display)
gap_mode_var.trace_add("write", on_gap_mode_change)

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

def make_rich_desc(parent, mode_val):
    t = tk.Text(
        parent, width=1, height=2, bg=BG_SUB, fg=DESC_TEXT, font=font(8, False),
        relief="flat", bd=0, highlightthickness=0, wrap="none", cursor="hand2",
        takefocus=0, selectbackground=BG_SUB, inactiveselectbackground=BG_SUB
    )
    t.tag_configure("amber", foreground=AMBER, font=font(8, True))
    t.tag_configure("bold", foreground=TEXT, font=font(8, True))
    t.bind("<Button-1>", lambda _: gap_mode_var.set(mode_val))
    t.config(state="disabled")
    return t

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

# Card 2: Thống kê thư mục
c2 = make_card(main)
make_lbl(c2, "Thống kê thư mục", anchor="w", padx=14, pady=(10, 4))
box = tk.Frame(c2, bg=BG_SUB, highlightbackground=BORDER, highlightthickness=1)
box.pack(fill="x", padx=14, pady=(2, 12))
lbl_total = make_lbl(box, "• Tổng số map (.map, .yrm, .mpr): Chưa quét thư mục", MUTED, 10, True, BG_SUB, fill="x", padx=10, pady=(6, 2))
lbl_num = make_lbl(box, "    ◦ Map đã được cấp số: --", MUTED, 9, True, BG_SUB, fill="x", padx=10, pady=1)
lbl_invalid_num = tk.Label(box, text="", bg=BG_SUB, fg=AMBER, font=font(9, False), anchor="w")
lbl_unnum = make_lbl(box, "    ◦ Map chưa được cấp số: --", MUTED, 9, True, BG_SUB, fill="x", padx=10, pady=(1, 6))
lbl_need_num = tk.Label(box, text="", bg=BG_SUB, fg=AMBER, font=font(9, True), anchor="w")
lbl_dup_note = tk.Label(box, text="", bg=BG_SUB, fg=MUTED, font=font(8, False), anchor="w", justify="left")

# Card 3: Đuôi file
c3 = make_card(main)
make_lbl(c3, "2. Định dạng đuôi muốn chuyển đổi thành", anchor="w", padx=14, pady=(10, 4))
radio_row = tk.Frame(c3, bg=BG_CARD)
radio_row.pack(anchor="w", padx=14, pady=(0, 10))
for ext in SOURCE_EXTS:
    ttk.Radiobutton(radio_row, text=ext, variable=ext_var, value=ext, style="Slate.TRadiobutton", takefocus=False, cursor="hand2").pack(side="left", padx=(0, 28))

# Card 4: Cấp số thứ tự
c4 = make_card(main)
make_lbl(c4, "3. Cấp số thứ tự đầu file (ví dụ: 1.arctic.map, 2.european.map)", anchor="w", padx=14, pady=(10, 4))
num_row = tk.Frame(c4, bg=BG_CARD)
num_row.pack(anchor="w", padx=14, pady=(0, 6))
make_lbl(num_row, "Cấp số mới cho map, bắt đầu từ:", side="left")
make_entry(num_row, start_var, fg=EMERALD, accent=EMERALD, width=6, justify="center", side="left", padx=8, ipady=2)

# Khung chọn 2 phương án xử lý số khuyết (tự động ẩn/hiện trong Mục 3)
gap_box = tk.Frame(c4, bg=BG_SUB, highlightbackground=AMBER, highlightthickness=1)
lbl_gap_title = make_lbl(gap_box, "⚠ Số thứ tự bị trống — Hãy chọn cách xử lý:", AMBER, 9, True, BG_SUB, fill="x", padx=10, pady=(6, 2))

ttk.Radiobutton(gap_box, text="Cách 1: Dồn lại số cho liền mạch & xếp map mới ở cuối", variable=gap_mode_var, value="compact", style="Sub.TRadiobutton", takefocus=False, cursor="hand2").pack(anchor="w", padx=10, pady=(2, 0))
txt_opt1_desc = make_rich_desc(gap_box, "compact")
txt_opt1_desc.pack(fill="x", padx=28, pady=(0, 5))

ttk.Radiobutton(gap_box, text="Cách 2: Giữ nguyên số cũ & lấp chỗ trống cho map mới", variable=gap_mode_var, value="fill", style="Sub.TRadiobutton", takefocus=False, cursor="hand2").pack(anchor="w", padx=10, pady=(2, 0))
txt_opt2_desc = make_rich_desc(gap_box, "fill")
txt_opt2_desc.pack(fill="x", padx=28, pady=(0, 8))

lbl_will_num = make_lbl(c4, "• Số lượng map sẽ cấp số: --", MUTED, 10, True, BG_CARD, fill="x", padx=14, pady=(2, 10))

# Nút xem trước kết quả đặt trung tâm ngay phía trên nút thực thi chính
preview_wrap = tk.Frame(main, bg=BG_CARD, highlightbackground=CYAN, highlightthickness=1)
btn_preview = tk.Button(
    preview_wrap, text="👁  Xem trước kết quả sau khi đổi", command=open_preview_window,
    bg=BG_CARD, fg=CYAN, activebackground="#273549", activeforeground="#FFFFFF",
    font=font(10, True), relief="flat", takefocus=False, cursor="hand2"
)
btn_preview.pack(fill="x", ipady=5)
btn_preview.bind("<Enter>", lambda _: btn_preview.config(bg="#273549"))
btn_preview.bind("<Leave>", lambda _: btn_preview.config(bg=BG_CARD))

# Nút thực thi chính
btn_run = make_btn(main, "BẮT ĐẦU ĐÁNH SỐ & CHUYỂN ĐỔI", process_files, PRIMARY, PRIMARY_HOVER, fill="x", pady=(2, 2), ipady=6)

resize_window()
apply_dark_titlebar(root)
root.after(10, lambda: apply_dark_titlebar(root))
root.mainloop()