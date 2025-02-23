import sys
import os
import cv2
import json
import numpy as np
import face_recognition
import shutil  # для видалення теки при видаленні обличчя

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QListWidget,
                               QFrame, QScrollArea, QDialog, QLineEdit, QTextEdit,
                               QDialogButtonBox, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QTimer, QSize, QEventLoop, QRect
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont, QShortcut, QKeySequence, QKeyEvent

video_capture_source = cv2.VideoCapture(int(input("Enter a videocapture source: ")))

# Допустимі розширення зображень
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

# ------------------ ДІАЛОГОВІ ВІКНА ------------------

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PyFaceID")
        self.setModal(True)
        self.resize(400, 400)

        layout = QVBoxLayout(self)

        title = QLabel("PyFaceID")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        description_text = (
            "PyFaceID is a facial recognition system written in Python using OpenCV and face_recognition library.\n"
            "The program allows you to capture, edit and save data about the face.\n"
            "It also provides quick access to functions using hotkeys."
        )
        description = QLabel(description_text)
        description.setWordWrap(True)
        layout.addWidget(description)

        hotkeys_text = (
            "Hotkeys:\n"
            "Capture (c) – Capture face\n"
            "Info (i) – View face information (read-only)\n"
            "Edit (e) – Edit face information\n"
            "Delete (d) – Delete face\n"
            "About (a) – Open this window\n"
            "Quit (q) – Exit the program\n"
            "(v) –Toggle face landmarks\n"
        )
        hotkeys_label = QLabel(hotkeys_text)
        hotkeys_label.setWordWrap(True)
        layout.addWidget(hotkeys_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


class CustomTextEdit(QTextEdit):
    """Кастомний QTextEdit, який не дозволяє табуляцію всередині."""
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Tab:
            self.focusNextPrevChild(True)  # Переміщення фокусу далі
        else:
            super().keyPressEvent(event)

class FaceDialog(QDialog):
    def __init__(self, face_pixmap, init_name="", init_description="", init_encoding=None, read_only=False, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Face Capture / Edit" if not read_only else "Face Capture / Edit / Info")
        self.setModal(True)
        self.resize(400, 500)

        self.face_pixmap = face_pixmap
        self.face_encoding = init_encoding

        layout = QVBoxLayout(self)

        self.face_label = QLabel()
        self.face_label.setAlignment(Qt.AlignCenter)
        if not face_pixmap.isNull():
            self.face_label.setPixmap(face_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.face_label)

        self.change_photo_btn = QPushButton("Change Photo")
        self.change_photo_btn.clicked.connect(self.change_photo)
        layout.addWidget(self.change_photo_btn)

        self.name_edit = QLineEdit(init_name)
        self.name_edit.setPlaceholderText("Enter name")
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_edit)

        self.desc_edit = CustomTextEdit()  # Використовуємо кастомний QTextEdit
        self.desc_edit.setPlainText(init_description)
        self.desc_edit.setPlaceholderText("Enter description")
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.desc_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.save_btn = self.button_box.button(QDialogButtonBox.Save)
        self.cancel_btn = self.button_box.button(QDialogButtonBox.Cancel)

        if self.save_btn:
            self.save_btn.setText("Save (Ctrl+S)")
            self.save_btn.clicked.connect(self.accept)

        if self.cancel_btn:
            self.cancel_btn.setText("Cancel (Esc)")
            self.cancel_btn.clicked.connect(self.reject)

        if read_only:
            self.name_edit.setDisabled(True)
            self.desc_edit.setDisabled(True)
            self.change_photo_btn.setDisabled(True)
            if self.save_btn:
                self.save_btn.setDisabled(True)

        # Встановлення порядку фокусу
        self.setTabOrder(self.name_edit, self.desc_edit)
        self.setTabOrder(self.desc_edit, self.save_btn)
        self.setTabOrder(self.save_btn, self.cancel_btn)
        self.setTabOrder(self.cancel_btn, self.change_photo_btn)
        self.setTabOrder(self.change_photo_btn, self.name_edit)  # Робимо цикл

        # Додаємо гарячу клавішу Ctrl+S для збереження
        self.shortcut_save = QShortcut("Ctrl+S", self)
        self.shortcut_save.activated.connect(self.accept)

        # Встановлюємо фокус на поле "Name" при відкритті
        self.name_edit.setFocus()

    def change_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.jpg *.jpeg *.png *.bmp)", options=QFileDialog.DontUseNativeDialog
        )
        if file_path:
            try:
                image = face_recognition.load_image_file(file_path)
                face_locations = face_recognition.face_locations(image, model="hog")
                if not face_locations:
                    QMessageBox.warning(self, "Error", "No face detected in the selected image.")
                    return
                top, right, bottom, left = face_locations[0]
                face_crop = image[top:bottom, left:right]
                encodings = face_recognition.face_encodings(image, [(top, right, bottom, left)])
                if not encodings:
                    QMessageBox.warning(self, "Error", "Unable to compute face encoding for the selected image.")
                    return
                encoding = encodings[0]
                new_pixmap = self.numpy2pixmap(face_crop)
                self.face_pixmap = new_pixmap
                self.face_encoding = encoding
                self.face_label.setPixmap(new_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error processing image: {e}")

    def numpy2pixmap(self, image_np):
        image_np = np.ascontiguousarray(image_np)
        h, w, ch = image_np.shape
        bytes_per_line = ch * w
        qt_image = QImage(image_np.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qt_image)

    def getData(self):
        return (self.name_edit.text(), self.desc_edit.toPlainText(), self.face_pixmap, self.face_encoding)

# ------------------ ГОЛОВНИЙ КЛАС ПРИЛОЖЕННЯ ------------------

class FaceRecognitionApp(QMainWindow):
    # Нові константи – дані зберігаються в теці face_data, а JSON-файл face_data.json знаходиться всередині
    FACE_DATA_FOLDER = "face_data"
    FACE_DATA_FILE = os.path.join(FACE_DATA_FOLDER, "face_data.json")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition System")
        self.showFullScreen()

        self.unknown_faces = []
        self.saved_faces = []
        self.next_unknown_id = 1
        self.draw_landmarks = False

        # --- Побудова графічного інтерфейсу ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(10)

        # Ліва частина – відео
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(0)

        video_container = QFrame()
        video_container.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        video_container.setLayout(QVBoxLayout())
        video_container.layout().setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        scroll_area.setWidget(self.video_label)

        video_container.layout().addWidget(scroll_area)
        left_layout.addWidget(video_container, stretch=1)

        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 10, 0, 0)

        self.capture_btn = QPushButton("Capture (c)")
        self.capture_btn.clicked.connect(self.capture_frames)
        bottom_layout.addWidget(self.capture_btn)

        left_layout.addWidget(bottom_panel, alignment=Qt.AlignBottom)
        main_layout.addWidget(left_widget, stretch=2)

        # Права частина – списки та кнопки
        right_widget = QWidget()
        right_widget.setFixedWidth(300)
        right_layout = QVBoxLayout(right_widget)

        right_layout.addWidget(QLabel("LIST CURRENT"))
        self.current_list = QListWidget()
        right_layout.addWidget(self.current_list)

        right_layout.addWidget(QLabel("ALL SAVED"))
        self.saved_list = QListWidget()
        right_layout.addWidget(self.saved_list)

        info_edit_layout = QHBoxLayout()
        self.info_btn = QPushButton("Info (i)")
        self.info_btn.clicked.connect(self.show_info)
        self.edit_btn = QPushButton("Edit (e)")
        self.edit_btn.clicked.connect(self.edit_face)
        info_edit_layout.addWidget(self.info_btn)
        info_edit_layout.addWidget(self.edit_btn)
        right_layout.addLayout(info_edit_layout)

        self.delete_btn = QPushButton("Delete (d)")
        self.delete_btn.clicked.connect(self.delete_face)
        right_layout.addWidget(self.delete_btn)

        about_quit_layout = QHBoxLayout()
        self.about_btn = QPushButton("About (a)")
        self.about_btn.clicked.connect(self.show_about)
        about_quit_layout.addWidget(self.about_btn)

        self.quit_btn = QPushButton("Quit (q)")
        self.quit_btn.clicked.connect(self.close)
        about_quit_layout.addWidget(self.quit_btn)
        right_layout.addLayout(about_quit_layout)

        main_layout.addWidget(right_widget, stretch=0)

        # --- Прив'язка клавіш через QShortcut ---
        self.shortcut_capture = QShortcut(QKeySequence(Qt.Key_C), self)
        self.shortcut_capture.activated.connect(self.capture_btn.click)

        self.shortcut_info = QShortcut(QKeySequence(Qt.Key_I), self)
        self.shortcut_info.activated.connect(self.info_btn.click)

        self.shortcut_edit = QShortcut(QKeySequence(Qt.Key_E), self)
        self.shortcut_edit.activated.connect(self.edit_btn.click)

        self.shortcut_delete = QShortcut(QKeySequence(Qt.Key_D), self)
        self.shortcut_delete.activated.connect(self.delete_btn.click)

        self.shortcut_about = QShortcut(QKeySequence(Qt.Key_A), self)
        self.shortcut_about.activated.connect(self.about_btn.click)

        self.shortcut_quit = QShortcut(QKeySequence(Qt.Key_Q), self)
        self.shortcut_quit.activated.connect(self.quit_btn.click)

        # --- Завантаження даних та налаштування відеопотоку ---
        self.load_saved_faces()
        self.scan_face_data_folder()

        # Якщо теки face_data немає – створюємо її
        if not os.path.exists(self.FACE_DATA_FOLDER):
            os.makedirs(self.FACE_DATA_FOLDER)

        self.capture = video_capture_source
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # приблизно 33 fps

        self.detection_model = "hog"

    def show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def show_info(self):
        selected_items = self.saved_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        face = next((f for f in self.saved_faces if f["name"] == item.text()), None)
        if face is None:
            return

        if face["pixmap"] is None and os.path.exists(face["image_path"]):
            face["pixmap"] = QPixmap(face["image_path"])

        dlg = FaceDialog(
            face_pixmap=face["pixmap"] if face["pixmap"] is not None else QPixmap(),
            init_name=face["name"],
            init_description=face["description"],
            init_encoding=face.get("encoding", None),
            read_only=True,
            parent=self
        )
        dlg.exec()

    def load_saved_faces(self):
        """Завантаження метаданих з JSON-файлу."""
        if not os.path.exists(self.FACE_DATA_FOLDER):
            os.makedirs(self.FACE_DATA_FOLDER)
            return
        if os.path.exists(self.FACE_DATA_FILE):
            try:
                with open(self.FACE_DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for face in data:
                    face["encoding"] = None
                    face["pixmap"] = None
                    self.saved_faces.append(face)
                    self.saved_list.addItem(face["name"])
            except Exception as e:
                print("Помилка завантаження збережених облич:", e)

    def save_saved_faces(self):
        try:
            data = []
            for face in self.saved_faces:
                data.append({
                    "id": face["id"],
                    "name": face["name"],
                    "description": face["description"],
                    "image_path": face.get("image_path", ""),
                    "encoding_path": face.get("encoding_path", "")
                })
            with open(self.FACE_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Помилка збереження облич:", e)

    def scan_face_data_folder(self):
        """
        Скануємо теку FACE_DATA_FOLDER. Якщо користувач додав зображення безпосередньо в цю теку,
        створюємо для нього окрему папку (назва за іменем файлу), переміщаємо зображення, обчислюємо кодування та додаємо дані у saved_faces.
        Також обробляємо вже існуючі підпапки.
        """
        if not os.path.exists(self.FACE_DATA_FOLDER):
            os.makedirs(self.FACE_DATA_FOLDER)
            return

        for entry in os.listdir(self.FACE_DATA_FOLDER):
            entry_path = os.path.join(self.FACE_DATA_FOLDER, entry)
            if os.path.isdir(entry_path):
                # Підпапка – вважаємо, що це обличчя
                image_file = None
                npy_file = None
                for file in os.listdir(entry_path):
                    file_path = os.path.join(entry_path, file)
                    ext = os.path.splitext(file)[1].lower()
                    if ext in IMAGE_EXTENSIONS:
                        image_file = file_path
                    elif ext == ".npy":
                        npy_file = file_path
                if image_file:
                    if not npy_file:
                        try:
                            image = face_recognition.load_image_file(image_file)
                            encodings = face_recognition.face_encodings(image)
                            if not encodings:
                                print(f"Обличчя не знайдено на зображенні: {image_file}")
                                continue
                            encoding = encodings[0]
                            npy_file = os.path.join(entry_path, f"{entry}.npy")
                            np.save(npy_file, encoding)
                            print(f"Кодування створено для {image_file}")
                        except Exception as e:
                            print(f"Помилка створення кодування для {image_file}: {e}")
                            continue
                    else:
                        encoding = np.load(npy_file)
                    pixmap = QPixmap(image_file)
                    face_entry = {
                        "id": self._get_next_id(),
                        "name": entry,
                        "description": "",
                        "image_path": image_file,
                        "encoding_path": npy_file,
                        "encoding": encoding,
                        "pixmap": pixmap
                    }
                    if not any(f["name"] == entry for f in self.saved_faces):
                        self.saved_faces.append(face_entry)
                        self.saved_list.addItem(entry)
            elif os.path.isfile(entry_path):
                # Якщо файл – перевіряємо чи це зображення (але не JSON)
                ext = os.path.splitext(entry)[1].lower()
                if ext in IMAGE_EXTENSIONS and entry.lower() != "face_data.json":
                    face_name = os.path.splitext(entry)[0]
                    face_folder = os.path.join(self.FACE_DATA_FOLDER, face_name)
                    if not os.path.exists(face_folder):
                        os.makedirs(face_folder)
                    new_image_path = os.path.join(face_folder, entry)
                    try:
                        os.rename(entry_path, new_image_path)
                    except Exception as e:
                        print(f"Не вдалося перемістити зображення {entry_path}: {e}")
                        continue
                    try:
                        image = face_recognition.load_image_file(new_image_path)
                        encodings = face_recognition.face_encodings(image)
                        if not encodings:
                            print(f"Обличчя не знайдено на зображенні: {new_image_path}")
                            continue
                        encoding = encodings[0]
                        npy_file = os.path.join(face_folder, f"{face_name}.npy")
                        np.save(npy_file, encoding)
                        print(f"Кодування створено для {new_image_path}")
                        pixmap = QPixmap(new_image_path)
                        face_entry = {
                            "id": self._get_next_id(),
                            "name": face_name,
                            "description": "",
                            "image_path": new_image_path,
                            "encoding_path": npy_file,
                            "encoding": encoding,
                            "pixmap": pixmap
                        }
                        if not any(f["name"] == face_name for f in self.saved_faces):
                            self.saved_faces.append(face_entry)
                            self.saved_list.addItem(face_name)
                    except Exception as e:
                        print(f"Помилка обробки зображення {new_image_path}: {e}")
                        continue

    def _get_next_id(self):
        if not self.saved_faces:
            return 1
        return max(face["id"] for face in self.saved_faces) + 1

    def update_frame(self):
        ret, frame = self.capture.read()
        if not ret:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model=self.detection_model)

        for face in self.unknown_faces:
            face["detected"] = False

        detected_faces = []
        for (top, right, bottom, left) in face_locations:
            x, y = left, top
            w, h = right - left, bottom - top

            encodings = face_recognition.face_encodings(rgb_frame, [(top, right, bottom, left)])
            if not encodings:
                continue
            encoding = encodings[0]

            landmarks = face_recognition.face_landmarks(rgb_frame, face_locations=[(top, right, bottom, left)])
            landmarks = landmarks[0] if landmarks else {}

            matched = False
            for face in self.saved_faces:
                if face["encoding"] is None:
                    if os.path.exists(face.get("encoding_path", "")):
                        face["encoding"] = np.load(face["encoding_path"])
                if face["encoding"] is not None:
                    match = face_recognition.compare_faces([face["encoding"]], encoding, tolerance=0.5)
                    if match[0]:
                        label = face["name"]
                        description = face["description"]
                        face["bbox"] = (x, y, w, h)
                        detected_faces.append({
                            "bbox": (x, y, w, h),
                            "label": label,
                            "description": description,
                            "landmarks": landmarks
                        })
                        matched = True
                        break
            if matched:
                continue

            for face in self.unknown_faces:
                match = face_recognition.compare_faces([face["encoding"]], encoding, tolerance=0.5)
                if match[0]:
                    face["bbox"] = (x, y, w, h)
                    crop = rgb_frame[y:y+h, x:x+w]
                    face["pixmap"] = self.numpy2pixmap(crop)
                    face["detected"] = True
                    detected_faces.append({
                        "bbox": (x, y, w, h),
                        "label": face["name"],
                        "description": face["description"],
                        "landmarks": landmarks
                    })
                    matched = True
                    break

            if not matched:
                face_id = self.next_unknown_id
                self.next_unknown_id += 1
                name = f"Unknown_{face_id}"
                crop = rgb_frame[y:y+h, x:x+w]
                face_entry = {
                    "id": face_id,
                    "encoding": encoding,
                            "bbox": (x, y, w, h),
            "pixmap": self.numpy2pixmap(crop),
                    "name": name,
                    "description": "",
                    "detected": True
                }
                self.unknown_faces.append(face_entry)
                detected_faces.append({
                    "bbox": (x, y, w, h),
                    "label": name,
                    "description": "",
                    "landmarks": landmarks
                })

        removed_faces = [face for face in self.unknown_faces if not face.get("detected", False)]
        for face in removed_faces:
            self.unknown_faces.remove(face)

        h_frame, w_frame, ch = rgb_frame.shape
        bytes_per_line = ch * w_frame
        qt_image = QImage(rgb_frame.data, w_frame, h_frame, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        container_size = self.video_label.parent().size()
        scaled_pixmap = pixmap.scaled(container_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        painter = QPainter(scaled_pixmap)
        scale_x = scaled_pixmap.width() / w_frame
        scale_y = scaled_pixmap.height() / h_frame

        for face in detected_faces:
            x, y, fw, fh = face["bbox"]
            rx = int(x * scale_x)
            ry = int(y * scale_y)
            rfw = int(fw * scale_x)
            rfh = int(fh * scale_y)

            if self.draw_landmarks:
                pen = QPen(QColor(0, 255, 0), 2)
                painter.setPen(pen)
                landmarks = face.get("landmarks", {})
                for feature, points in landmarks.items():
                    for point in points:
                        px = int(point[0] * scale_x)
                        py = int(point[1] * scale_y)
                        painter.drawEllipse(px - 2, py - 2, 4, 4)
            else:
                pen = QPen(QColor(0, 255, 0))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawRect(rx, ry, rfw, rfh)

            # Зовнішні відступи (margin) для різних сторін:
            external_offset_left = 8            # відступ від лівої межі обличчя до текстового блоку
            external_offset_name = 8            # відступ від верхньої межі обличчя до блоку з ім'ям
            external_offset_description = 8     # відступ від нижньої межі обличчя до блоку з описом

            # Внутрішній відступ (padding) всередині блоку з текстом:
            internal_padding = 4

            # Змінна для регулювання округлення кутів:
            border_radius = 10

            fm = painter.fontMetrics()

            # Рендеринг заголовка (ім'я) над обличчям:
            label = face["label"]
            label_width = fm.horizontalAdvance(label)
            label_height = fm.height()

            label_bg_width = label_width + 2 * internal_padding
            label_bg_height = label_height + 2 * internal_padding
            # Нижня межа блоку з ім'ям буде external_offset_name пікселів вище верхньої межі обличчя
            label_bg_bottom = ry - external_offset_name
            label_bg_top = max(label_bg_bottom - label_bg_height, 0)
            label_bg_x = rx + external_offset_left

            label_background_rect = QRect(label_bg_x, label_bg_top, label_bg_width, label_bg_height)

            # Вмикаємо згладжування для кращої якості округлених кутів
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 255, 0))
            painter.drawRoundedRect(label_background_rect, border_radius, border_radius)
            painter.setPen(Qt.black)

            label_text_rect = QRect(
                label_background_rect.left() + internal_padding,
                label_background_rect.top() + internal_padding,
                label_width,
                label_height
            )
            painter.drawText(label_text_rect, Qt.AlignLeft | Qt.AlignVCenter, label)

            # Рендеринг опису під обличчям:
            if face["description"]:
                description_lines = face["description"].splitlines()
                max_line_width = max(fm.horizontalAdvance(line) for line in description_lines)
                total_text_height = len(description_lines) * label_height

                desc_bg_x = rx + external_offset_left
                desc_bg_y = ry + rfh + external_offset_description
                desc_bg_width = max_line_width + 2 * internal_padding
                desc_bg_height = total_text_height + 2 * internal_padding

                desc_background_rect = QRect(desc_bg_x, desc_bg_y, desc_bg_width, desc_bg_height)
                
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 255, 0))
                painter.drawRoundedRect(desc_background_rect, border_radius, border_radius)
                painter.setPen(Qt.black)

                for idx, line in enumerate(description_lines):
                    line_y = desc_background_rect.top() + internal_padding + idx * label_height
                    line_rect = QRect(
                        desc_background_rect.left() + internal_padding,
                        line_y,
                        max_line_width,
                        label_height
                    )
                    painter.drawText(line_rect, Qt.AlignLeft | Qt.AlignVCenter, line)



        painter.end()
        self.video_label.setPixmap(scaled_pixmap)

        self.current_list.clear()
        for face in detected_faces:
            self.current_list.addItem(face["label"])

    def numpy2pixmap(self, image_np):
        if image_np is None or image_np.size == 0:
            return QPixmap()
        image_np = np.ascontiguousarray(image_np)
        h, w, ch = image_np.shape
        bytes_per_line = ch * w
        qt_image = QImage(image_np.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qt_image)

    def capture_frames(self):
        unknowns = self.unknown_faces.copy()
        for face in unknowns:
            dlg = FaceDialog(
                face_pixmap=face["pixmap"],
                init_name=face["name"],
                init_description=face["description"],
                init_encoding=face.get("encoding", None),
                parent=self
            )
            result = dlg.exec()
            if result == QDialog.Accepted:
                new_name, description, new_pixmap, new_encoding = dlg.getData()
                old_name = face["name"]
                if new_name:
                    face["name"] = new_name
                face["description"] = description
                if new_pixmap is not None and not new_pixmap.isNull():
                    face["pixmap"] = new_pixmap
                if new_encoding is not None:
                    face["encoding"] = new_encoding

                # Створюємо (або перейменовуємо) теку для обличчя
                face_folder = os.path.join(self.FACE_DATA_FOLDER, face["name"])
                if not os.path.exists(face_folder):
                    old_face_folder = os.path.join(self.FACE_DATA_FOLDER, old_name)
                    if os.path.exists(old_face_folder):
                        os.rename(old_face_folder, face_folder)
                    else:
                        os.makedirs(face_folder)
                image_save_path = os.path.join(face_folder, f"{face['name']}.jpg")
                encoding_save_path = os.path.join(face_folder, f"{face['name']}.npy")

                face["pixmap"].save(image_save_path, "JPG")
                np.save(encoding_save_path, face["encoding"])
                face["image_path"] = image_save_path
                face["encoding_path"] = encoding_save_path

                self.saved_faces.append(face)
                self.unknown_faces = [f for f in self.unknown_faces if f["id"] != face["id"]]
                self._remove_item_from_list(self.current_list, face["name"])
                self.saved_list.addItem(face["name"])
            loop = QEventLoop()
            QTimer.singleShot(100, loop.quit)
            loop.exec()

    def _remove_item_from_list(self, list_widget, text):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.text() == text:
                list_widget.takeItem(i)
                break

    def edit_face(self):
        selected_items = self.saved_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        face = next((f for f in self.saved_faces if f["name"] == item.text()), None)
        if face is None:
            return

        if face["pixmap"] is None and os.path.exists(face["image_path"]):
            face["pixmap"] = QPixmap(face["image_path"])

        dlg = FaceDialog(
            face_pixmap=face["pixmap"] if face["pixmap"] is not None else QPixmap(),
            init_name=face["name"],
            init_description=face["description"],
            init_encoding=face.get("encoding", None),
            parent=self
        )
        result = dlg.exec()
        if result == QDialog.Accepted:
            new_name, description, new_pixmap, new_encoding = dlg.getData()
            old_name = face["name"]
            if new_name:
                face["name"] = new_name
            face["description"] = description
            if new_pixmap is not None and not new_pixmap.isNull():
                face["pixmap"] = new_pixmap
            if new_encoding is not None:
                face["encoding"] = new_encoding

            old_face_folder = os.path.join(self.FACE_DATA_FOLDER, old_name)
            new_face_folder = os.path.join(self.FACE_DATA_FOLDER, face["name"])
            if old_face_folder != new_face_folder and os.path.exists(old_face_folder):
                os.rename(old_face_folder, new_face_folder)
            else:
                if not os.path.exists(new_face_folder):
                    os.makedirs(new_face_folder)
            image_save_path = os.path.join(new_face_folder, f"{face['name']}.jpg")
            encoding_save_path = os.path.join(new_face_folder, f"{face['name']}.npy")
            face["pixmap"].save(image_save_path, "JPG")
            np.save(encoding_save_path, face["encoding"])
            face["image_path"] = image_save_path
            face["encoding_path"] = encoding_save_path

            item.setText(face["name"])

    def delete_face(self):
        selected_items = self.saved_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        face_to_delete = next((face for face in self.saved_faces if face["name"] == item.text()), None)
        if face_to_delete is None:
            return

        face_folder = os.path.join(self.FACE_DATA_FOLDER, face_to_delete["name"])
        if os.path.exists(face_folder):
            try:
                shutil.rmtree(face_folder)
                print(f"Видалено папку обличчя: {face_folder}")
            except Exception as e:
                print(f"Не вдалося видалити папку {face_folder}: {e}")

        self.saved_faces = [face for face in self.saved_faces if face["name"] != item.text()]
        self.saved_list.takeItem(self.saved_list.row(item))

    def closeEvent(self, event):
        self.capture.release()
        self.save_saved_faces()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_V:
            self.draw_landmarks = not self.draw_landmarks
            print("Режим landmarks:", self.draw_landmarks)
        super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FaceRecognitionApp()
    sys.exit(app.exec())
