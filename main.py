import customtkinter as ctk
import os
import shutil
import threading
import time
import platform
from tkinter import filedialog, messagebox
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class OrganizerHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
        
    def on_created(self, event):
        if not event.is_directory:
            time.sleep(1.5) 
            self.app.after(0, lambda: self.app.organize_logic(event.src_path))

class FileOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VORTEX SORT")
        self.geometry("850x750")

        self.history = []  
        self.extension_map = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.tiff'],
            'Documents': ['.pdf', '.docx', '.txt', '.xlsx', '.pptx', '.csv', '.odt', '.rtf'],
            'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv'],
            'Music': ['.mp3', '.wav', '.flac', '.m4a', '.ogg'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            'Packages': ['.exe', '.msi', '.bat', '.deb', '.rpm', '.sh', '.bin', '.run']
        }
        
        self.observer = None
        self.is_watching = False

        self.setup_ui()

    def setup_ui(self):
        self.label = ctk.CTkLabel(self, text="VORTEX SORT", font=ctk.CTkFont(size=28, weight="bold"))
        self.label.pack(pady=10)

        self.dev_label = ctk.CTkLabel(self, text="Developed by Kivanc", font=ctk.CTkFont(size=12, slant="italic"), text_color="#3b82f6")
        self.dev_label.pack(pady=(0, 20))

        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.pack(fill="x", padx=40, pady=10)
        
        self.path_entry = ctk.CTkEntry(self.path_frame, placeholder_text="Select folder to organize...", width=550)
        self.path_entry.pack(side="left", padx=10, pady=15)
        
        self.browse_btn = ctk.CTkButton(self.path_frame, text="Browse", width=100, command=self.browse_folder)
        self.browse_btn.pack(side="right", padx=10)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=40, pady=10)

        self.organize_btn = ctk.CTkButton(self.btn_frame, text="ORGANIZE NOW", fg_color="#10b981", 
                                          hover_color="#059669", font=ctk.CTkFont(weight="bold"), command=self.start_manual_organize)
        self.organize_btn.pack(side="left", expand=True, padx=5, fill="x")

        self.undo_btn = ctk.CTkButton(self.btn_frame, text="↩ UNDO ALL ACTIONS", fg_color="#334155", 
                                       command=self.undo_last_action)
        self.undo_btn.pack(side="left", expand=True, padx=5, fill="x")

        self.watch_switch = ctk.CTkSwitch(self, text="Real-time Watch Mode (Auto-Organize)", 
                                          font=ctk.CTkFont(size=14), command=self.toggle_watcher)
        self.watch_switch.pack(pady=15)

        self.rule_container = ctk.CTkFrame(self)
        self.rule_container.pack(fill="x", padx=40, pady=10)
        
        tk_title = ctk.CTkLabel(self.rule_container, text="Add New Priority Rule", font=ctk.CTkFont(weight="bold"))
        tk_title.pack(pady=5)

        self.cat_input = ctk.CTkEntry(self.rule_container, placeholder_text="Folder Name", width=150)
        self.cat_input.pack(side="left", padx=10, pady=10, expand=True)
        
        self.ext_input = ctk.CTkEntry(self.rule_container, placeholder_text="Extensions (e.g. .jpg, .pdf)", width=300)
        self.ext_input.pack(side="left", padx=10, pady=10, expand=True)
        
        self.add_btn = ctk.CTkButton(self.rule_container, text="Update Rule", width=120, command=self.add_custom_rule)
        self.add_btn.pack(side="left", padx=10, pady=10)

        self.log_box = ctk.CTkTextbox(self, height=200, font=("Consolas", 11), fg_color="#000000")
        self.log_box.pack(fill="both", padx=40, pady=20)
        
        self.status_label = ctk.CTkLabel(self, text="System ready.", text_color="gray")
        self.status_label.pack(side="bottom", pady=5)

    def log(self, message):
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_box.see("end")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, folder)
            self.log(f"Selected folder: {folder}")

    def add_custom_rule(self):
        cat = self.cat_input.get().strip()
        exts_raw = self.ext_input.get().strip().split(',')
        
        if cat and exts_raw != [""]:
            new_exts = [e.strip().lower() if e.strip().startswith('.') else f".{e.strip().lower()}" for e in exts_raw]
            
            existing_exts = self.extension_map.get(cat, [])
            combined_exts = list(set(existing_exts + new_exts))
            
            if cat in self.extension_map:
                del self.extension_map[cat]
            
            new_map = {cat: combined_exts}
            new_map.update(self.extension_map)
            self.extension_map = new_map
            
            self.log(f"PRIORITY UPDATED: '{cat}' prioritized with: {combined_exts}")
            self.cat_input.delete(0, 'end')
            self.ext_input.delete(0, 'end')
            messagebox.showinfo("Success", f"Rule for '{cat}' has been updated.")
        else:
            messagebox.showwarning("Error", "Check input fields!")

    def organize_logic(self, file_path):
        if not os.path.isfile(file_path): return
        
        filename = os.path.basename(file_path)
        lower_name = filename.lower()
        
        # Cross-platform system file ignore list
        ignore_list = ('dumpstack', '$', 'desktop.ini', 'thumbs.db', '.ds_store', '.git', '.tmp')
        if lower_name.startswith(ignore_list) or lower_name.startswith('.'): return

        file_ext = os.path.splitext(lower_name)[1]
        target_dir = os.path.dirname(file_path)
        
        found_category = "Others"
        for category, extensions in self.extension_map.items():
            if file_ext in extensions:
                found_category = category
                break
        
        dest_folder = os.path.join(target_dir, found_category)
        if not os.path.exists(dest_folder):
            try:
                os.makedirs(dest_folder)
            except:
                self.log(f"PERMISSION DENIED: Could not create {found_category}")
                return
        
        dest_path = os.path.join(dest_folder, filename)
        
        counter = 1
        base_name, extension = os.path.splitext(filename)
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_folder, f"{base_name}_{counter}{extension}")
            counter += 1

        try:
            shutil.move(file_path, dest_path)
            self.history.append((file_path, dest_path)) 
            self.log(f"MOVED: {filename} >>> {found_category}")
        except Exception as e:
            self.log(f"ERROR: {filename} failed | {str(e)}")

    def start_manual_organize(self):
        target = self.path_entry.get()
        if not os.path.exists(target):
            messagebox.showerror("Error", "Invalid path!")
            return
        
        self.log(">>> Manual organization started.")
        try:
            files = [os.path.join(target, f) for f in os.listdir(target) if os.path.isfile(os.path.join(target, f))]
            for f in files:
                self.organize_logic(f)
            self.log(">>> Manual organization finished.")
            messagebox.showinfo("Finished", "Folder organized successfully.")
        except Exception as e:
            messagebox.showerror("Critical Error", str(e))

    def undo_last_action(self):
        if not self.history:
            messagebox.showinfo("Info", "No history found.")
            return
        
        self.log("<<< Undo process started...")
        count = 0
        while self.history:
            old_path, current_path = self.history.pop()
            try:
                if not os.path.exists(os.path.dirname(old_path)):
                    os.makedirs(os.path.dirname(old_path))
                shutil.move(current_path, old_path)
                count += 1
            except:
                self.log(f"ERROR: Could not restore {os.path.basename(current_path)}")
        
        self.log(f"<<< Total {count} actions undone.")
        messagebox.showinfo("Success", f"{count} files restored.")

    def toggle_watcher(self):
        target = self.path_entry.get()
        if not os.path.exists(target):
            self.watch_switch.deselect()
            messagebox.showerror("Error", "Select folder first!")
            return

        if self.watch_switch.get():
            self.is_watching = True
            self.log("WATCH MODE: ACTIVE.")
            self.observer = Observer()
            self.observer.schedule(OrganizerHandler(self), target, recursive=False)
            self.observer.start()
        else:
            if self.observer:
                self.observer.stop()
                self.observer.join()
            self.is_watching = False
            self.log("WATCH MODE: DISABLED.")

if __name__ == "__main__":
    app = FileOrganizerApp()
    app.mainloop()
