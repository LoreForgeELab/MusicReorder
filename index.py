import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
# PIL is required to display .png or .jpg files in Tkinter
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None

class MusicReorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MP3 Sequence Editor")
        self.root.geometry("600x750")
        self.root.configure(bg="#f0f0f0")

        self.folder_path = ""
        self.curIndex = None
        self.filenames_raw = [] # Keep original names without selection markers
        
        # --- Logo and Title Section ---
        self.logo_frame = tk.Frame(root, bg="#f0f0f0")
        self.logo_frame.pack(pady=5, fill="x")

        # Set window icon and handle title branding
        self.load_logo_and_icon()

        # --- UI Header ---
        self.header_frame = tk.Frame(root, bg="#f0f0f0")
        self.header_frame.pack(pady=10, fill="x")

        self.btn_select = tk.Button(
            self.header_frame, 
            text="📁 Select MP3 Folder", 
            command=self.select_folder,
            font=("Arial", 10, "bold"),
            padx=10
        )
        self.btn_select.pack()

        self.lbl_path = tk.Label(self.header_frame, text="No folder selected", fg="gray", bg="#f0f0f0", wraplength=550)
        self.lbl_path.pack(pady=5)

        # --- Selection Control Bar ---
        self.ctrl_frame = tk.Frame(root, bg="#f0f0f0")
        self.ctrl_frame.pack(fill="x", padx=20)

        self.var_select_all = tk.BooleanVar()
        self.chk_all = tk.Checkbutton(
            self.ctrl_frame, 
            text="Select All / Deselect All", 
            variable=self.var_select_all,
            command=self.toggle_select_all,
            bg="#f0f0f0",
            font=("Arial", 9)
        )
        self.chk_all.pack(side=tk.LEFT)

        self.lbl_info = tk.Label(
            self.ctrl_frame, 
            text="(Right-Click to Drag & Reorder)",
            font=("Arial", 8, "italic"),
            bg="#f0f0f0",
            fg="#777"
        )
        self.lbl_info.pack(side=tk.RIGHT)

        # --- Scrollable Listbox Frame ---
        self.list_frame = tk.Frame(root)
        self.list_frame.pack(expand=True, fill="both", padx=20, pady=5)
        
        self.scrollbar = tk.Scrollbar(self.list_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            self.list_frame, 
            selectmode=tk.MULTIPLE, 
            font=("Consolas", 11),
            activestyle='none',
            selectbackground="#3498db",
            yscrollcommand=self.scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, expand=True, fill="both")
        self.scrollbar.config(command=self.listbox.yview)

        # Bindings
        self.listbox.bind('<<ListboxSelect>>', self.update_visual_selection)
        self.listbox.bind('<Button-3>', self.on_start_drag)
        self.listbox.bind('<B3-Motion>', self.on_drag_motion)
        self.listbox.bind('<ButtonRelease-3>', self.on_stop_drag)

        # --- Footer ---
        self.button_frame = tk.Frame(root, bg="#f0f0f0")
        self.button_frame.pack(pady=15, fill="x", padx=20)

        self.btn_erase = tk.Button(
            self.button_frame, 
            text="Erase Numbers (Selected)", 
            command=self.erase_numbers, 
            bg="#e74c3c", 
            fg="white",
            font=("Arial", 10, "bold"),
            pady=8,
            cursor="hand2"
        )
        self.btn_erase.pack(side=tk.LEFT, expand=True, fill="x", padx=(0, 5))

        self.btn_rename = tk.Button(
            self.button_frame, 
            text="Rename & Re-index (Selected)", 
            command=self.rename_files, 
            bg="#2ecc71", 
            fg="white",
            font=("Arial", 10, "bold"),
            pady=8,
            cursor="hand2"
        )
        self.btn_rename.pack(side=tk.LEFT, expand=True, fill="x", padx=(5, 0))

    def load_logo_and_icon(self):
        """Sets MusicReorder.png as window icon and removes the large UI logo."""
        try:
            logo_path = "MusicReorder.png"
            if Image and os.path.exists(logo_path):
                img_file = Image.open(logo_path)
                
                # --- Set Window Icon (Top Left Corner) ---
                self.icon_img = ImageTk.PhotoImage(img_file)
                self.root.iconphoto(True, self.icon_img) 
                
                # Large Logo label is removed as per request to keep it only in corner
            else:
                raise Exception("Icon file missing")
        except Exception:
            pass # Fallback to default Tkinter icon behavior

    def select_folder(self):
        selected = filedialog.askdirectory()
        if selected:
            self.folder_path = selected
            self.lbl_path.config(text=f"Folder: {self.folder_path}")
            self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        if not self.folder_path:
            return
        
        files = [f for f in os.listdir(self.folder_path) if f.lower().endswith('.mp3')]
        files.sort()
        self.filenames_raw = files
        
        for f in files:
            self.listbox.insert(tk.END, f"[ ] {f}")
        
        self.var_select_all.set(False)

    def toggle_select_all(self):
        if self.var_select_all.get():
            self.listbox.selection_set(0, tk.END)
        else:
            self.listbox.selection_clear(0, tk.END)
        self.update_visual_selection()

    def update_visual_selection(self, event=None):
        """Updates the [ ] or [✓] prefix based on selection state."""
        selected_indices = self.listbox.curselection()
        for i in range(self.listbox.size()):
            clean_name = self.filenames_raw[i]
            if i in selected_indices:
                self.listbox.delete(i)
                self.listbox.insert(i, f"[✓] {clean_name}")
                self.listbox.selection_set(i)
            else:
                current_text = self.listbox.get(i)
                if "[✓]" in current_text:
                    self.listbox.delete(i)
                    self.listbox.insert(i, f"[ ] {clean_name}")

    # --- Drag and Drop Logic (Right Click) ---
    def on_start_drag(self, event):
        index = self.listbox.nearest(event.y)
        if index >= 0:
            self.curIndex = index
            self.listbox.itemconfig(index, bg="#d1e7dd") 

    def on_drag_motion(self, event):
        i = self.listbox.nearest(event.y)
        if i != self.curIndex and self.curIndex is not None:
            text = self.listbox.get(self.curIndex)
            raw_text = self.filenames_raw.pop(self.curIndex)
            is_selected = self.listbox.selection_includes(self.curIndex)
            
            self.listbox.delete(self.curIndex)
            self.listbox.insert(i, text)
            self.filenames_raw.insert(i, raw_text)
            
            if is_selected:
                self.listbox.selection_set(i)
            
            self.curIndex = i

    def on_stop_drag(self, event):
        if self.curIndex is not None:
            self.listbox.itemconfig(self.curIndex, bg="white")
        self.curIndex = None

    def erase_numbers(self):
        if not self.folder_path:
            messagebox.showwarning("Warning", "Please select a folder first!")
            return

        indices = self.listbox.curselection()
        if not indices:
            messagebox.showinfo("Info", "No files selected.")
            return

        if messagebox.askyesno("Confirm Erase", f"Remove numbers from {len(indices)} selected files?"):
            try:
                for i in indices:
                    filename = self.filenames_raw[i]
                    old_path = os.path.join(self.folder_path, filename)
                    clean_name = re.sub(r'^\d+[\s._-]*', '', filename)
                    new_path = os.path.join(self.folder_path, clean_name)
                    
                    if old_path != new_path and not os.path.exists(new_path):
                        os.rename(old_path, new_path)
                
                messagebox.showinfo("Success", "Cleaned selected files!")
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def rename_files(self):
        if not self.folder_path:
            messagebox.showwarning("Warning", "Please select a folder first!")
            return

        indices = self.listbox.curselection()
        if not indices:
            messagebox.showinfo("Info", "No files selected.")
            return

        if messagebox.askyesno("Confirm Rename", f"Re-index {len(indices)} selected files using their list position?"):
            try:
                for i in range(self.listbox.size()):
                    if i not in indices:
                        continue
                    
                    row_number = i + 1
                    filename = self.filenames_raw[i]
                    old_path = os.path.join(self.folder_path, filename)
                    clean_name = re.sub(r'^\d+[\s._-]*', '', filename)
                    
                    new_name = f"{row_number:02d} {clean_name}"
                    new_path = os.path.join(self.folder_path, new_name)
                    
                    if old_path != new_path:
                        if os.path.exists(new_path):
                            temp = os.path.join(self.folder_path, f"tmp_{row_number}_{clean_name}")
                            os.rename(old_path, temp)
                            os.rename(temp, new_path)
                        else:
                            os.rename(old_path, new_path)
                
                messagebox.showinfo("Success", "Selected files renamed!")
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicReorderApp(root)
    root.mainloop()
