import cv2
import face_recognition
import numpy as np
import json
import os
from tkinter import Tk, Label, Entry, Button, StringVar, Listbox, Toplevel, messagebox

# Шлях до файлу для зберігання даних про обличчя
DATA_FILE = "face_data.json"

# Завантаження або створення файлу з даними
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        face_data = json.load(f)
else:
    face_data = {}

# Функція для збереження даних у файл
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(face_data, f)

# Функція для додавання нового обличчя
def add_new_face(face_id, unknown_faces):
    def save_face():
        name = name_entry.get()
        params = params_entry.get()

        if not name:
            messagebox.showerror("Помилка", "Ім'я не може бути порожнім!")
            return

        # Отримання енкодінгу обличчя за face_id
        face_encoding = unknown_faces[face_id]["encoding"]

        # Збереження даних
        face_data[name] = {
            "encoding": face_encoding.tolist(),  # Перетворення numpy array у список
            "params": params
        }

        # Збереження даних у файл
        save_data()

        # Оновлення списків для відображення
        known_face_encodings.append(face_encoding)
        known_face_names.append(name)
        known_face_params.append(params)

        # Видалення обличчя зі словника невідомих
        del unknown_faces[face_id]

        messagebox.showinfo("Успіх", f"Обличчя {name} додано!")
        root.destroy()  # Закриття вікна після збереження
        update_face_list()  # Оновлення списку облич

    # Створення графічного інтерфейсу
    root = Toplevel()
    root.title("Додати нове обличчя")

    # Поля для введення даних
    Label(root, text=f"Призначити ім'я для обличчя {unknown_faces[face_id]['name']}:").grid(row=0, column=0, columnspan=2, padx=10, pady=10)
    Label(root, text="Ім'я:").grid(row=1, column=0, padx=10, pady=10)
    name_entry = Entry(root)
    name_entry.grid(row=1, column=1, padx=10, pady=10)

    Label(root, text="Параметри:").grid(row=2, column=0, padx=10, pady=10)
    params_entry = Entry(root)
    params_entry.grid(row=2, column=1, padx=10, pady=10)

    # Кнопка для збереження
    Button(root, text="Зберегти", command=save_face).grid(row=3, column=0, columnspan=2, pady=10)

# Функція для редагування обличчя
def edit_face():
    selected = face_listbox.curselection()
    if not selected:
        messagebox.showerror("Помилка", "Виберіть обличчя для редагування!")
        return

    selected_name = face_listbox.get(selected[0])

    def save_edit():
        new_name = name_entry.get()
        new_params = params_entry.get()

        if not new_name:
            messagebox.showerror("Помилка", "Ім'я не може бути порожнім!")
            return

        # Оновлення даних
        face_data[new_name] = face_data.pop(selected_name)
        face_data[new_name]["params"] = new_params

        # Збереження даних у файл
        save_data()

        # Оновлення списків
        index = known_face_names.index(selected_name)
        known_face_names[index] = new_name
        known_face_params[index] = new_params

        messagebox.showinfo("Успіх", f"Обличчя {selected_name} оновлено!")
        edit_window.destroy()  # Закриття вікна після збереження
        update_face_list()  # Оновлення списку облич

    # Створення графічного інтерфейсу для редагування
    edit_window = Toplevel()
    edit_window.title("Редагування обличчя")

    # Поля для введення даних
    Label(edit_window, text="Ім'я:").grid(row=0, column=0, padx=10, pady=10)
    name_entry = Entry(edit_window)
    name_entry.insert(0, selected_name)
    name_entry.grid(row=0, column=1, padx=10, pady=10)

    Label(edit_window, text="Параметри:").grid(row=1, column=0, padx=10, pady=10)
    params_entry = Entry(edit_window)
    params_entry.insert(0, face_data[selected_name]["params"])
    params_entry.grid(row=1, column=1, padx=10, pady=10)

    # Кнопка для збереження
    Button(edit_window, text="Зберегти", command=save_edit).grid(row=2, column=0, columnspan=2, pady=10)

# Функція для видалення обличчя
def delete_face():
    selected = face_listbox.curselection()
    if not selected:
        messagebox.showerror("Помилка", "Виберіть обличчя для видалення!")
        return

    selected_name = face_listbox.get(selected[0])

    # Видалення обличчя зі словника
    del face_data[selected_name]

    # Збереження даних у файл
    save_data()

    # Оновлення списків
    index = known_face_names.index(selected_name)
    known_face_encodings.pop(index)
    known_face_names.pop(index)
    known_face_params.pop(index)

    messagebox.showinfo("Успіх", f"Обличчя {selected_name} видалено!")
    update_face_list()

# Функція для оновлення списку облич
def update_face_list():
    selected_index = face_listbox.curselection()  # Зберігаємо вибраний елемент
    face_listbox.delete(0, "end")
    # Додаємо відомі обличчя
    for name in known_face_names:
        face_listbox.insert("end", name)
    # Додаємо невідомі обличчя
    for face_id, data in unknown_faces.items():
        face_listbox.insert("end", data["name"])
    # Відновлюємо вибраний елемент
    if selected_index:
        face_listbox.selection_set(selected_index[0])

# Завантаження енкодінгів з файлу
known_face_encodings = []
known_face_names = []
known_face_params = []

for name, data in face_data.items():
    known_face_encodings.append(np.array(data["encoding"]))
    known_face_names.append(name)
    known_face_params.append(data["params"])

# Запуск веб-камери
cap = cv2.VideoCapture(2)

# Словник для зберігання тимчасових даних про невідомі обличчя
unknown_faces = {}  # {face_id: {"encoding": encoding, "name": "Unknown_X"}}
unknown_counter = 1  # Лічильник для унікальних ідентифікаторів

# Створення головного вікна для відеопотоку
root = Tk()
root.title("Face Recognition")

# Створення вікна для списку облич
list_window = Toplevel(root)
list_window.title("Список облич")

# Список облич
face_listbox = Listbox(list_window)
face_listbox.pack(padx=10, pady=10)

# Кнопки для редагування та видалення
Button(list_window, text="Редагувати", command=edit_face).pack(side="left", padx=10, pady=10)
Button(list_window, text="Видалити", command=delete_face).pack(side="right", padx=10, pady=10)

# Оновлення списку облич
update_face_list()

# Змінна для відстеження змін у списку облич
last_face_count = len(known_face_names) + len(unknown_faces)

while True:
    # Зчитування кадру з веб-камери
    ret, frame = cap.read()
    if not ret:
        print("Помилка захоплення кадру!")
        break

    # Знаходження облич у кадрі
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    # Оновлення списку невідомих облич
    unknown_faces = {}  # Очищаємо словник невідомих облич
    unknown_counter = 1  # Скидаємо лічильник

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = None
        params = ""

        # Якщо знайдено збіг
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
            params = known_face_params[first_match_index]
        else:
            # Якщо обличчя невідоме, додаємо його до словника
            face_id = f"Unknown_{unknown_counter}"
            unknown_counter += 1
            unknown_faces[face_id] = {"encoding": face_encoding, "name": face_id}
            name = face_id

        # Малювання прямокутника навколо обличчя
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Відображення імені та параметрів
        label = f"{name} - {params}" if params else name
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # Відображення кадру
    cv2.imshow('Face Recognition', frame)

    # Оновлення списку облич, якщо кількість облич змінилася
    current_face_count = len(known_face_names) + len(unknown_faces)
    if current_face_count != last_face_count:
        update_face_list()
        last_face_count = current_face_count

    # Обробка натискання клавіш
    key = cv2.waitKey(1)
    if key == ord('q'):  # Вихід
        break
    elif key == ord('c'):  # Додати нове обличчя
        if unknown_faces:
            # Відкриваємо вікно для введення даних для першого невідомого обличчя
            face_id = list(unknown_faces.keys())[0]  # Беремо перше невідоме обличчя
            add_new_face(face_id, unknown_faces)

    # Оновлення графічного інтерфейсу
    root.update()

# Звільнення ресурсів
cap.release()
cv2.destroyAllWindows()
root.destroy()
