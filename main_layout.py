import sys
import cv2
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QListWidget, 
                             QFrame, QScrollArea)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QImage, QPixmap

videocapture_source = int(input("Enter a videocapture source: "))

class FaceRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition System")
        self.showFullScreen()
        
        # Створюємо головний віджет і layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(10)
        
        # Ліва частина (відео)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(0)
        
        # Створюємо контейнер для відео з фіксованим розміром
        video_container = QFrame()
        video_container.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        video_container.setLayout(QVBoxLayout())
        video_container.layout().setContentsMargins(0, 0, 0, 0)
        
        # Створюємо QScrollArea для контролю розміру відео
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Відеопотік
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        scroll_area.setWidget(self.video_label)
        
        video_container.layout().addWidget(scroll_area)
        
        # Додаємо відео-контейнер з політикою розширення
        left_layout.addWidget(video_container, stretch=1)
        
        # Нижня панель з контролями
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 10, 0, 0)
        
        # Кнопка захоплення
        self.capture_btn = QPushButton("Capture (c)")
        self.capture_btn.clicked.connect(self.capture_frame)
        bottom_layout.addWidget(self.capture_btn)
        
        # Додаємо нижню панель без розтягування
        left_layout.addWidget(bottom_panel, alignment=Qt.AlignBottom)
        
        main_layout.addWidget(left_widget, stretch=2)
        
        # Права частина (списки і кнопки)
        right_widget = QWidget()
        right_widget.setFixedWidth(300)
        right_layout = QVBoxLayout(right_widget)
        
        # Поточний список
        right_layout.addWidget(QLabel("LIST CURRENT"))
        self.current_list = QListWidget()
        right_layout.addWidget(self.current_list)
        
        # Збережений список
        right_layout.addWidget(QLabel("ALL SAVED"))
        self.saved_list = QListWidget()
        right_layout.addWidget(self.saved_list)
        
        # Кнопки
        self.edit_btn = QPushButton("Edit (e)")
        self.delete_btn = QPushButton("Delete (d)")
        self.quit_btn = QPushButton("Quit (q)")
        self.quit_btn.clicked.connect(self.close)
        
        right_layout.addWidget(self.edit_btn)
        right_layout.addWidget(self.delete_btn)
        right_layout.addWidget(self.quit_btn)
        
        main_layout.addWidget(right_widget, stretch=0)
        
        # Налаштування відеопотоку
        self.capture = cv2.VideoCapture(videocapture_source)
        
        # Таймер для оновлення кадрів
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30ms = ~33 fps
        
        # Налаштування розпізнавання облич
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            # Визначаємо обличчя
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            # Малюємо прямокутники навколо облич
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Конвертуємо в формат Qt
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Отримуємо розмір контейнера
            container_size = self.video_label.parent().size()
            
            # Масштабуємо зображення під розмір контейнера
            scaled_pixmap = pixmap.scaled(container_size, 
                                        Qt.KeepAspectRatio, 
                                        Qt.SmoothTransformation)
            
            self.video_label.setPixmap(scaled_pixmap)
    
    def capture_frame(self):
        # Тут можна додати логіку збереження кадру
        pass
    
    def closeEvent(self, event):
        self.capture.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FaceRecognitionApp()
    sys.exit(app.exec())