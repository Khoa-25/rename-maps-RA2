import os
import tkinter as tk
from tkinter import filedialog, messagebox

def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_path.set(folder_selected)

def convert_extensions():
    target_dir = folder_path.get()
    target_ext = selected_ext.get()
    source_exts = ('.map', '.yrm', '.mpr')

    if not target_dir or not os.path.isdir(target_dir):
        messagebox.showerror("Lỗi", "Vui lòng chọn một thư mục hợp lệ!")
        return

    count = 0
    errors = []

    try:
        for filename in os.listdir(target_dir):
            if filename.lower().endswith(source_exts):
                base_name, current_ext = os.path.splitext(filename)

                if current_ext.lower() == target_ext:
                    continue

                old_file = os.path.join(target_dir, filename)
                new_file = os.path.join(target_dir, base_name + target_ext)

                if os.path.exists(new_file):
                    errors.append(f"Bỏ qua '{filename}' vì '{base_name + target_ext}' đã tồn tại.")
                    continue

                os.rename(old_file, new_file)
                count += 1

        msg = f"Hoàn tất! Đã chuyển đổi thành công {count} file sang đuôi '{target_ext}'."
        if errors:
            msg += "\n\nCác file bị bỏ qua do trùng tên:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n...và {len(errors) - 5} file khác."
        
        messagebox.showinfo("Kết quả", msg)

    except Exception as e:
        messagebox.showerror("Lỗi hệ thống", f"Đã xảy ra lỗi: {str(e)}")

# --- Khởi tạo giao diện ---
root = tk.Tk()
root.title("Công cụ đổi đuôi Map (RA2 / Yuri's Revenge)")
root.geometry("450x230")
root.resizable(False, False)

folder_path = tk.StringVar()
selected_ext = tk.StringVar(value=".map")  # Mặc định chọn .map

# Phần 1: Chọn thư mục
tk.Label(root, text="1. Chọn thư mục chứa file (.map, .yrm, .mpr):", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 5))

frame_dir = tk.Frame(root)
frame_dir.pack(fill="x", padx=20)

entry_dir = tk.Entry(frame_dir, textvariable=folder_path, width=42)
entry_dir.pack(side="left", padx=(0, 10))

btn_browse = tk.Button(frame_dir, text="Browse...", command=browse_folder)
btn_browse.pack(side="left")

# Phần 2: Chọn đuôi đích
tk.Label(root, text="2. Chọn định dạng đuôi muốn chuyển đổi thành:", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 5))

frame_radio = tk.Frame(root)
frame_radio.pack(anchor="w", padx=30)

extensions = [(".map", ".map"), (".yrm", ".yrm"), (".mpr", ".mpr")]
for text, ext in extensions:
    tk.Radiobutton(frame_radio, text=text, variable=selected_ext, value=ext, font=("Arial", 10)).pack(side="left", padx=(0, 20))

# Phần 3: Nút thực thi
btn_run = tk.Button(root, text="Bắt đầu chuyển đổi", command=convert_extensions, bg="#0078D7", fg="white", font=("Arial", 10, "bold"), padx=15, pady=5)
btn_run.pack(pady=20)

root.mainloop()