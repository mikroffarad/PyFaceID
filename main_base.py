import sys
import os
import cv2
import json
import numpy as np
import face_recognition

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QListWidget, 
                               QFrame, QScrollArea, QDialog, QLineEdit, QTextEdit, 
                               QDialogButtonBox, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QTimer, QSize, QEventLoop, QRect
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont, QShortcut, QKeySequence

# Вибір джерела відео (наприклад, 0 для вебкамери)
videocapture_source = int(input("Enter a videocapture source: "))

# Допустимі розширення зображень
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

class FaceDialog(QDialog):
    """
    Діалогове вікно для введення/редагування інформації про обличчя.
    Показує зображення обличчя, поле для імені та опису.
    Додано кнопку "Change Photo" для зміни зображення.
    """
    def __init__(self, face_pixmap, init_name="", init_description="", init_encoding=None, read_only=False, parent=None):
        super().__init__(parent)

        # Встановлюємо заголовок в залежності від режиму
        if read_only:
            self.setWindowTitle("Face Capture / Edit / Info")
        else:
            self.setWindowTitle("Face Capture / Edit")

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

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlainText(init_description)
        self.desc_edit.setPlaceholderText("Enter description")
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.desc_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Якщо режим тільки для перегляду, відключаємо редагування
        if read_only:
            self.name_edit.setDisabled(True)
            self.desc_edit.setDisabled(True)
            self.change_photo_btn.setDisabled(True)
            save_btn = self.button_box.button(QDialogButtonBox.Save)
            if save_btn:
                save_btn.setDisabled(True)

    def change_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.jpg *.jpeg *.png *.bmp)",
            options=QFileDialog.DontUseNativeDialog
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
        return (self.name_edit.text(),
                self.desc_edit.toPlainText(),
                self.face_pixmap,
                self.face_encoding)


class FaceRecognitionApp(QMainWindow):
    # Файл для збереження метаданих (без кодування)
    SAVED_FACES_FILE = "saved_faces.json"  
    # Папка, де зберігаються зображення та файли з кодуванням
    SAVED_FACES_FOLDER = "saved_faces"     
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition System")
        self.showFullScreen()
        # Списки для відстеження облич та інші змінні...
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

        # Створюємо кнопки "Info" та "Edit" в одному рядку
        buttons_layout = QHBoxLayout()
        self.info_btn = QPushButton("Info (i)")
        self.info_btn.clicked.connect(self.show_info)
        self.edit_btn = QPushButton("Edit (e)")
        self.edit_btn.clicked.connect(self.edit_face)
        buttons_layout.addWidget(self.info_btn)
        buttons_layout.addWidget(self.edit_btn)
        right_layout.addLayout(buttons_layout)

        self.delete_btn = QPushButton("Delete (d)")
        self.delete_btn.clicked.connect(self.delete_face)
        self.quit_btn = QPushButton("Quit (q)")
        self.quit_btn.clicked.connect(self.close)

        right_layout.addWidget(self.delete_btn)
        right_layout.addWidget(self.quit_btn)

        main_layout.addWidget(right_widget, stretch=0)

        self.shortcut_capture = QShortcut(QKeySequence(Qt.Key_C), self)
        self.shortcut_capture.activated.connect(self.capture_btn.click)

        self.shortcut_info = QShortcut(QKeySequence(Qt.Key_I), self)
        self.shortcut_info.activated.connect(self.info_btn.click)

        self.shortcut_edit = QShortcut(QKeySequence(Qt.Key_E), self)
        self.shortcut_edit.activated.connect(self.edit_btn.click)

        self.shortcut_delete = QShortcut(QKeySequence(Qt.Key_D), self)
        self.shortcut_delete.activated.connect(self.delete_btn.click)

        self.shortcut_quit = QShortcut(QKeySequence(Qt.Key_Q), self)
        self.shortcut_quit.activated.connect(self.quit_btn.click)

        # --- Після побудови інтерфейсу завантажуємо дані ---
        self.load_saved_faces()
        self.scan_saved_faces_folder()

        # Налаштування відеопотоку
        self.capture = cv2.VideoCapture(videocapture_source)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # приблизно 33 fps

        self.detection_model = "hog"

    # Метод для перегляду інформації (read‑only режим)
    def show_info(self):
        selected_items = self.saved_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        face = next((f for f in self.saved_faces if f["name"] == item.text()), None)
        if face is None:
            return

        # Якщо pixmap не завантажено – завантажуємо з image_path
        if face["pixmap"] is None and os.path.exists(face["image_path"]):
            face["pixmap"] = QPixmap(face["image_path"])

        dlg = FaceDialog(
            face_pixmap=face["pixmap"] if face["pixmap"] is not None else QPixmap(),
            init_name=face["name"],
            init_description=face["description"],
            init_encoding=face.get("encoding", None),
            read_only=True,  # Вказуємо, що це лише для перегляду
            parent=self
        )
        dlg.exec()
    
    def load_saved_faces(self):
        """Завантаження метаданих з JSON-файлу."""
        if os.path.exists(self.SAVED_FACES_FILE):
            try:
                with open(self.SAVED_FACES_FILE, "r") as f:
                    data = json.load(f)
                for face in data:
                    # Спочатку кодування не завантажуємо – воно буде завантажено із окремого файлу
                    face["encoding"] = None  
                    face["pixmap"] = None
                    self.saved_faces.append(face)
                    self.saved_list.addItem(face["name"])
            except Exception as e:
                print("Помилка завантаження збережених облич:", e)
    
    def scan_saved_faces_folder(self):
        """
        Скануємо папку SAVED_FACES_FOLDER на наявність зображень.
        Якщо для зображення не існує файлу з кодуванням, створюємо його,
        після чого записуємо дані (якщо запису ще нема) у saved_faces.
        """
        if not os.path.exists(self.SAVED_FACES_FOLDER):
            os.makedirs(self.SAVED_FACES_FOLDER)
            return
        
        # Отримуємо вже завантажені імена (з saved_faces)
        existing_names = {face["name"] for face in self.saved_faces}
        for filename in os.listdir(self.SAVED_FACES_FOLDER):
            name, ext = os.path.splitext(filename)
            if ext.lower() not in IMAGE_EXTENSIONS:
                continue
            image_path = os.path.join(self.SAVED_FACES_FOLDER, filename)
            encoding_save_path = os.path.join(self.SAVED_FACES_FOLDER, f"{name}.npy")
            if not os.path.exists(encoding_save_path):
                try:
                    # Завантажуємо зображення та обчислюємо кодування
                    image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(image)
                    if not encodings:
                        print(f"Обличчя не знайдено на зображенні: {image_path}")
                        continue
                    encoding = encodings[0]
                    # Зберігаємо кодування у файл
                    np.save(encoding_save_path, encoding)
                    print(f"Кодування створено для {image_path}")
                except Exception as e:
                    print(f"Помилка створення кодування для {image_path}: {e}")
                    continue
            # Якщо запису ще нема – додаємо запис до saved_faces
            if name not in existing_names:
                try:
                    encoding = np.load(encoding_save_path)
                    # Завантажуємо зображення у QPixmap
                    pixmap = QPixmap(image_path)
                    face_entry = {
                        "id": self._get_next_id(),
                        "name": name,
                        "description": "",
                        "image_path": image_path,
                        "encoding_path": encoding_save_path,
                        "encoding": encoding,
                        "pixmap": pixmap  # збережемо завантажене зображення
                    }
                    self.saved_faces.append(face_entry)
                    self.saved_list.addItem(face_entry["name"])
                    print(f"Завантажено обличчя: {image_path}")
                except Exception as e:
                    print(f"Помилка завантаження обличчя {image_path}: {e}")

    
    def _get_next_id(self):
        """Повертає наступний унікальний ідентифікатор."""
        if not self.saved_faces:
            return 1
        return max(face["id"] for face in self.saved_faces) + 1
    
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
            with open(self.SAVED_FACES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Помилка збереження облич:", e)

    
    def update_frame(self):
        ret, frame = self.capture.read()
        if not ret:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model=self.detection_model)

        # Скидаємо прапорець "detected" у невідомих облич
        for face in self.unknown_faces:
            face["detected"] = False

        detected_faces = []
        # Обходимо кожну знайдену область обличчя
        for (top, right, bottom, left) in face_locations:
            x, y = left, top
            w, h = right - left, bottom - top

            encodings = face_recognition.face_encodings(rgb_frame, [(top, right, bottom, left)])
            if not encodings:
                continue
            encoding = encodings[0]

            # Отримуємо landmarks для цього обличчя (для поточної області)
            landmarks = face_recognition.face_landmarks(rgb_frame, face_locations=[(top, right, bottom, left)])
            if landmarks:
                landmarks = landmarks[0]
            else:
                landmarks = {}

            # Пошук серед збережених облич
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

            # Пошук серед невідомих облич
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
                # Нова невідома особа – додаємо до списку невідомих
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

        # Видаляємо невиявлені обличчя зі списку невідомих
        removed_faces = [face for face in self.unknown_faces if not face.get("detected", False)]
        for face in removed_faces:
            self.unknown_faces.remove(face)

        # Підготовка зображення для відображення
        h_frame, w_frame, ch = rgb_frame.shape
        bytes_per_line = ch * w_frame
        qt_image = QImage(rgb_frame.data, w_frame, h_frame, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        container_size = self.video_label.parent().size()
        scaled_pixmap = pixmap.scaled(container_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        painter = QPainter(scaled_pixmap)
        scale_x = scaled_pixmap.width() / w_frame
        scale_y = scaled_pixmap.height() / h_frame

        # Для кожного обличчя відображаємо або landmarks, або рамку – але текст (ім'я та опис) відображається завжди.
        for face in detected_faces:
            x, y, fw, fh = face["bbox"]
            rx = int(x * scale_x)
            ry = int(y * scale_y)
            rfw = int(fw * scale_x)
            rfh = int(fh * scale_y)

            if self.draw_landmarks:
                # Режим landmarks: малюємо зелені точки для кожного landmark
                pen = QPen(QColor(0, 255, 0), 2)  # зелений колір, товщина 2
                painter.setPen(pen)
                landmarks = face.get("landmarks", {})
                for feature, points in landmarks.items():
                    for point in points:
                        px = int(point[0] * scale_x)
                        py = int(point[1] * scale_y)
                        painter.drawEllipse(px - 2, py - 2, 4, 4)
            else:
                # Режим рамок: малюємо зелену рамку навколо обличчя
                pen = QPen(QColor(0, 255, 0))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawRect(rx, ry, rfw, rfh)

            # Відображення імені (label)
            label = face["label"]
            fm = painter.fontMetrics()
            text_width = fm.horizontalAdvance(label)
            text_height = fm.height()
            padding = 4  # відступ для зручного відображення
            background_rect = QRect(rx, max(ry - text_height - 2 * padding, 0), text_width + 2 * padding, text_height + 2 * padding)
            painter.fillRect(background_rect, QColor(0, 255, 0))
            painter.setPen(Qt.black)
            painter.drawText(background_rect, Qt.AlignCenter, label)

            # Відображення опису (якщо є)
            if face["description"]:
                description_lines = face["description"].splitlines()
                for i, line in enumerate(description_lines):
                    line_width = fm.horizontalAdvance(line)
                    line_rect = QRect(rx, ry + rfh + i * (text_height + padding), line_width + 2 * padding, text_height + 2 * padding)
                    painter.fillRect(line_rect, QColor(0, 255, 0))
                    painter.setPen(Qt.black)
                    painter.drawText(line_rect, Qt.AlignCenter, line)

        painter.end()
        self.video_label.setPixmap(scaled_pixmap)

        # Оновлюємо список "LIST CURRENT"
        self.current_list.clear()
        for face in detected_faces:
            self.current_list.addItem(face["label"])

    
    def numpy2pixmap(self, image_np):
        """Конвертує numpy-масив (RGB) у QPixmap."""
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
                name, description, new_pixmap, new_encoding = dlg.getData()
                face["name"] = name if name else face["name"]
                face["description"] = description
                if new_pixmap is not None and not new_pixmap.isNull():
                    face["pixmap"] = new_pixmap
                if new_encoding is not None:
                    face["encoding"] = new_encoding

                # Формуємо шляхи збереження за новим іменем (якщо ім'я змінено)
                image_save_path = os.path.join(self.SAVED_FACES_FOLDER, f"{face['name']}.jpg")
                encoding_save_path = os.path.join(self.SAVED_FACES_FOLDER, f"{face['name']}.npy")

                if not os.path.exists(self.SAVED_FACES_FOLDER):
                    os.makedirs(self.SAVED_FACES_FOLDER)
                
                # Зберігаємо нову фотографію та кодування – вони перезапишуть старі файли
                face["pixmap"].save(image_save_path, "JPG")
                np.save(encoding_save_path, face["encoding"])
                
                # Оновлюємо метадані – зберігаємо шляхи до файлів
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

        # Якщо pixmap не завантажено – завантажуємо з image_path
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
            name, description, new_pixmap, new_encoding = dlg.getData()
            face["name"] = name if name else face["name"]
            face["description"] = description
            if new_pixmap is not None and not new_pixmap.isNull():
                face["pixmap"] = new_pixmap
            if new_encoding is not None:
                face["encoding"] = new_encoding

            # Формуємо нові шляхи для збереження (якщо ім'я змінено)
            image_save_path = os.path.join(self.SAVED_FACES_FOLDER, f"{face['name']}.jpg")
            encoding_save_path = os.path.join(self.SAVED_FACES_FOLDER, f"{face['name']}.npy")
            
            # Зберігаємо нові фотографію та кодування
            face["pixmap"].save(image_save_path, "JPG")
            np.save(encoding_save_path, face["encoding"])
            
            # Оновлюємо метадані – шляхи до файлів
            face["image_path"] = image_save_path
            face["encoding_path"] = encoding_save_path

            item.setText(face["name"])


    
    def delete_face(self):
        selected_items = self.saved_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        # Знаходимо запис обличчя за ім'ям
        face_to_delete = next((face for face in self.saved_faces if face["name"] == item.text()), None)
        if face_to_delete is None:
            return

        # Видаляємо файли, якщо вони існують
        image_path = face_to_delete.get("image_path", "")
        encoding_path = face_to_delete.get("encoding_path", "")

        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
                print(f"Видалено файл зображення: {image_path}")
            except Exception as e:
                print(f"Не вдалося видалити файл {image_path}: {e}")

        if encoding_path and os.path.exists(encoding_path):
            try:
                os.remove(encoding_path)
                print(f"Видалено файл кодування: {encoding_path}")
            except Exception as e:
                print(f"Не вдалося видалити файл {encoding_path}: {e}")

        # Видаляємо запис з saved_faces
        self.saved_faces = [face for face in self.saved_faces if face["name"] != item.text()]
        # Видаляємо елемент зі списку "ALL SAVED"
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
