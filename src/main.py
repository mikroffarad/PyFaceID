import cv2
import face_recognition
import os
import numpy as np

def capture_and_recognize_faces():
    # Ініціалізація відеокамери
    video_capture = cv2.VideoCapture(0)

    # Створення директорії для збереження облич, якщо вона не існує
    if not os.path.exists('known_faces'):
        os.makedirs('known_faces')

    known_face_encodings = []
    known_face_names = []

    # Завантаження збережених облич
    for filename in os.listdir('known_faces'):
        filepath = os.path.join('known_faces', filename)
        image = face_recognition.load_image_file(filepath)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            encoding = encodings[0]
            known_face_encodings.append(encoding)
            name = os.path.splitext(filename)[0]
            known_face_names.append(name)
        else:
            print(f"Не вдалося знайти обличчя на зображенні {filename}. Перевірте файл.")

    while True:
        # Захоплення кадру
        ret, frame = video_capture.read()

        # Пошук облич на кадрі
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Розпізнавання облич
        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            face_names.append(name)

        # Малювання прямокутників та підписів
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Додавання інструкцій на екран
        instructions = "Press 'c' to capture face, 'q' to quit"
        cv2.putText(frame, instructions, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Показ кадру
        cv2.imshow('Face Recognition', frame)

        # Обробка натискань клавіш
        key = cv2.waitKey(1) & 0xFF

        # Натиснення 'c' для захоплення обличчя
        if key == ord('c'):
            user_name = input("Введіть ваше ім'я: ")
            if user_name:
                if face_locations:
                    top, right, bottom, left = face_locations[0]
                    face_image = frame[top:bottom, left:right]

                    # Зберігаємо зображення обличчя
                    filename = f'known_faces/{user_name}.jpg'
                    cv2.imwrite(filename, face_image)

                    # Оновлення списку збережених облич
                    image = face_recognition.load_image_file(filename)
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        encoding = encodings[0]
                        known_face_encodings.append(encoding)
                        known_face_names.append(user_name)
                        print(f"Обличчя збережено як {filename}")
                    else:
                        print(f"Не вдалося знайти обличчя на зображенні {filename}. Перевірте якість зображення.")
                        os.remove(filename)  # Видалити некоректне зображення

                    # Показуємо повідомлення на екрані
                    cv2.putText(frame, "Face Captured!", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.imshow('Face Recognition', frame)
                    cv2.waitKey(1000)  # Показуємо повідомлення на секунду

        # Вихід при натисканні 'q'
        elif key == ord('q'):
            break

    # Звільнення ресурсів
    video_capture.release()
    cv2.destroyAllWindows()

# Запуск функції
if __name__ == "__main__":
    capture_and_recognize_faces()
