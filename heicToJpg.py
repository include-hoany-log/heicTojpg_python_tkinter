
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os
import threading
import concurrent.futures
import sys
from pathlib import Path
from PIL import Image, ImageTk
from pillow_heif import register_heif_opener

# HEIC 포맷 지원 활성화
register_heif_opener()

class HeicConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Heic To Jpg / Png")
        self.root.resizable(False, False)
        
        # 윈도우 창 타이틀바 및 작업표시줄 아이콘 설정
        # PyInstaller로 패키징 시 풀리는 임시 경로(_MEIPASS) 대응
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent
            
        icon_path = base_path / "heicToJpg.ico"
        if icon_path.exists():
            self.root.iconbitmap(default=str(icon_path))

        self.source_dir = None
        self.file_list = []
        
        self.image_types = {
            "JPEG": {"format": "JPEG", "ext": ".jpg"},
            "PNG": {"format": "PNG", "ext": ".png"}
        }
        
        self.photo_ref = None # 가비지 컬렉션 방지용 이미지 참조
        self.current_preview_path = None # 현재 선택된 프리뷰 파일 경로 (빠른 선택 전환 처리용)

        self._build_ui()

    def _build_ui(self):
        # Row 0
        self.sourceSelectButton = tk.Button(self.root, width=20, text="HEIC 파일 폴더 선택", command=self.select_directory)
        self.sourceSelectButton.grid(row=0, column=0, padx=10, pady=10, sticky='news')

        self.imageTypeCombo = ttk.Combobox(self.root, values=list(self.image_types.keys()), state='readonly')
        self.imageTypeCombo.set("JPEG")
        self.imageTypeCombo.grid(row=0, column=1, padx=10, pady=10, sticky='news')

        self.sourceDirectoryLabel = tk.Label(self.root, width=70, anchor='w', text="HEIC 파일 폴더 선택")
        self.sourceDirectoryLabel.grid(row=0, column=2, padx=10, pady=10, sticky='news')

        # Row 1
        self.fileListbox = tk.Listbox(self.root, width=35, height=15, selectmode=tk.SINGLE)
        self.fileListbox.bind('<<ListboxSelect>>', self.handle_selection)
        self.fileListbox.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky='news')

        # Row 2
        self.canvas = tk.Canvas(self.root, width=600, height=300, bg="white")
        self.canvas.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky='news')

        # Row 3
        self.exifInfoLabel = tk.Label(self.root, width=40, anchor='w', text="EXIF 정보")
        self.exifInfoLabel.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky='news')

        # Row 4
        self.progressVar = tk.DoubleVar()
        self.progressBar = ttk.Progressbar(self.root, variable=self.progressVar, maximum=100)
        self.progressBar.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky='news')

        self.convertButton = tk.Button(self.root, text="전체 HEIC 변환", command=self.start_conversion_thread)
        self.convertButton.grid(row=4, column=2, padx=10, pady=10, sticky='news')

    def select_directory(self):
        selected = filedialog.askdirectory()
        if selected:
            self.source_dir = Path(selected)
            self.sourceDirectoryLabel.config(text=f"HEIC 파일 폴더: {self.source_dir}")
            self.update_file_list()

    def update_file_list(self):
        self.fileListbox.delete(0, tk.END)
        self.file_list.clear()
        
        if not self.source_dir:
            return
            
        for file in self.source_dir.iterdir():
            if file.suffix.lower() == '.heic':
                self.file_list.append(file.name)
                self.fileListbox.insert(tk.END, file.name)

    def handle_selection(self, event):
        selected_index = self.fileListbox.curselection()
        if not selected_index:
            return
            
        selected_file = self.fileListbox.get(selected_index)
        heic_file_path = self.source_dir / selected_file
        
        self.current_preview_path = heic_file_path
        
        # 즉각적인 반응을 위해 로딩 상태 즉시 표시
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width() or 600
        canvas_height = self.canvas.winfo_height() or 300
        self.canvas.create_text(canvas_width // 2, canvas_height // 2, text="미리보기 로딩 중...", fill="gray")
        self.exifInfoLabel.config(text="EXIF 정보 로딩 중...")
        
        # UI가 멈추지 않도록 백그라운드 스레드에서 이미지 로드 및 리사이징 실행
        thread = threading.Thread(target=self._process_preview_async, args=(heic_file_path, canvas_width, canvas_height), daemon=True)
        thread.start()

    def _process_preview_async(self, path, width, height):
        try:
            with Image.open(path) as image:
                # 1. EXIF 데이터 추출
                exif = image.getexif()
                make = exif.get(271, "알 수 없음")
                model = exif.get(316, "알 수 없음")
                date = exif.get(306, "알 수 없음")
                exif_text = f"[제조사: {make}] [촬영기종: {model}] [촬영일자: {date}]"

                # 2. 이미지 리사이징 (thumbnail을 이용해 최적화 비율 축소)
                image.thumbnail((width, height))
                
                # 스레드 전환 중에 사용자가 다른 파일을 클릭했는지 검사 (마지막 선택 파일만 로드)
                if self.current_preview_path == path:
                    # with 블록을 빠져나가면 image 객체가 닫히므로 copy() 후 메인스레드 전달
                    self.root.after(0, self._update_preview_ui, path, image.copy(), exif_text)
        except Exception as e:
            if self.current_preview_path == path:
                self.root.after(0, self._update_preview_ui_error, path, str(e))

    def _update_preview_ui(self, path, resized_image, exif_text):
        if self.current_preview_path != path:
            return
            
        # ImageTk 객체는 반드시 메인 스레드에서 생성해야 정상 동작함
        self.photo_ref = ImageTk.PhotoImage(resized_image)
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width() or 600
        canvas_height = self.canvas.winfo_height() or 300
        self.canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.photo_ref, anchor='center')
        self.exifInfoLabel.config(text=exif_text)

    def _update_preview_ui_error(self, path, error_msg):
        if self.current_preview_path != path:
            return
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width() or 600
        canvas_height = self.canvas.winfo_height() or 300
        self.canvas.create_text(canvas_width // 2, canvas_height // 2, text="이미지 미리보기 실패", fill="red")
        self.exifInfoLabel.config(text="[EXIF 정보 파싱 실패]")

    def start_conversion_thread(self):
        if not self.source_dir or not self.file_list:
            messagebox.showwarning("알림", "변환할 파일이 존재하지 않거나 폴더가 선택되지 않았습니다.")
            return
            
        # 중복 실행 방지
        self.convertButton.config(state=tk.DISABLED)
        self.progressVar.set(0)
        
        thread = threading.Thread(target=self.process_conversion, daemon=True)
        thread.start()

    def process_conversion(self):
        img_type_key = self.imageTypeCombo.get()
        img_format = self.image_types[img_type_key]["format"]
        img_ext = self.image_types[img_type_key]["ext"]
        
        output_dir = self.source_dir / img_format
        output_dir.mkdir(exist_ok=True)

        increment = 100.0 / len(self.file_list)
        success_count = 0
        
        # cpu_count가 None일 때를 대비하여 안전한 워커 갯수 산정
        cpu_cores = os.cpu_count() or 1
        max_workers = max(1, round(cpu_cores * 0.7))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.convert_file, f, output_dir, img_format, img_ext) for f in self.file_list]
            
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    success_count += 1
                # 스레드 안전성(Thread-Safety) 확보: 메인 스레드(GUI)에게 프로그레스 바 업데이트를 위임
                self.root.after(0, self.update_progress_bar, increment)

        # 변환 완료 후 메인 스레드에서 UI를 업데이트 하도록 위임
        self.root.after(0, self.conversion_finished, success_count)

    def convert_file(self, file_name, output_dir, img_format, img_ext):
        try:
            heic_file_path = self.source_dir / file_name
            out_file_path = output_dir / f"{Path(file_name).stem}{img_ext}"
            
            with Image.open(heic_file_path) as image:
                icc_profile = image.info.get("icc_profile")
                exif = image.getexif()
                image.save(out_file_path, format=img_format, exif=exif, icc_profile=icc_profile)
            return True
        except Exception as e:
            print(f"변환 실패 ({file_name}): {e}")
            return False

    def update_progress_bar(self, amount):
        self.progressVar.set(self.progressVar.get() + amount)

    def conversion_finished(self, success_count):
        self.progressVar.set(100)
        self.convertButton.config(state=tk.NORMAL)
        total = len(self.file_list)
        if success_count == total:
            messagebox.showinfo("알림", f"모든 파일 변환 완료 ({success_count}/{total})")
        else:
            messagebox.showwarning("알림", f"일부 파일 변환 실패\n성공: {success_count} / 전체: {total}")

def main():
    root = tk.Tk()
    app = HeicConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
