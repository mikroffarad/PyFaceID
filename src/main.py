import cv2
import face_recognition
import numpy as np
import json
import os
from tkinter import Tk, Label, Entry, Button, StringVar, Listbox, Toplevel, messagebox

# Path to the file for storing face data
DATA_FILE = "face_data.json"

# Load or create the data file
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        face_data = json.load(f)
else:
    face_data = {}

# Function to save data to the file
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(face_data, f)

# Function to add a new face
def add_new_face(face_id, unknown_faces):
    def save_face():
        name = name_entry.get()
        params = params_entry.get()

        if not name:
            messagebox.showerror("Error", "Name cannot be empty!")
            return

        # Get the face encoding by face_id
        face_encoding = unknown_faces[face_id]["encoding"]

        # Save the data
        face_data[name] = {
            "encoding": face_encoding.tolist(),  # Convert numpy array to list
            "params": params
        }

        # Save data to the file
        save_data()

        # Update the lists for display
        known_face_encodings.append(face_encoding)
        known_face_names.append(name)
        known_face_params.append(params)

        # Remove the face from the unknown faces dictionary
        del unknown_faces[face_id]

        messagebox.showinfo("Success", f"Face {name} added!")
        root.destroy()  # Close the window after saving
        update_face_list()  # Update the face list

    # Create the GUI
    root = Toplevel()
    root.title("Add New Face")

    # Input fields
    Label(root, text=f"Assign a name for face {unknown_faces[face_id]['name']}:").grid(row=0, column=0, columnspan=2, padx=10, pady=10)
    Label(root, text="Name:").grid(row=1, column=0, padx=10, pady=10)
    name_entry = Entry(root)
    name_entry.grid(row=1, column=1, padx=10, pady=10)

    Label(root, text="Parameters:").grid(row=2, column=0, padx=10, pady=10)
    params_entry = Entry(root)
    params_entry.grid(row=2, column=1, padx=10, pady=10)

    # Save button
    Button(root, text="Save", command=save_face).grid(row=3, column=0, columnspan=2, pady=10)

# Function to edit a face
def edit_face():
    selected = face_listbox.curselection()
    if not selected:
        messagebox.showerror("Error", "Select a face to edit!")
        return

    selected_name = face_listbox.get(selected[0])

    def save_edit():
        new_name = name_entry.get()
        new_params = params_entry.get()

        if not new_name:
            messagebox.showerror("Error", "Name cannot be empty!")
            return

        # Update the data
        face_data[new_name] = face_data.pop(selected_name)
        face_data[new_name]["params"] = new_params

        # Save data to the file
        save_data()

        # Update the lists
        index = known_face_names.index(selected_name)
        known_face_names[index] = new_name
        known_face_params[index] = new_params

        messagebox.showinfo("Success", f"Face {selected_name} updated!")
        edit_window.destroy()  # Close the window after saving
        update_face_list()  # Update the face list

    # Create the GUI for editing
    edit_window = Toplevel()
    edit_window.title("Edit Face")

    # Input fields
    Label(edit_window, text="Name:").grid(row=0, column=0, padx=10, pady=10)
    name_entry = Entry(edit_window)
    name_entry.insert(0, selected_name)
    name_entry.grid(row=0, column=1, padx=10, pady=10)

    Label(edit_window, text="Parameters:").grid(row=1, column=0, padx=10, pady=10)
    params_entry = Entry(edit_window)
    params_entry.insert(0, face_data[selected_name]["params"])
    params_entry.grid(row=1, column=1, padx=10, pady=10)

    # Save button
    Button(edit_window, text="Save", command=save_edit).grid(row=2, column=0, columnspan=2, pady=10)

# Function to delete a face
def delete_face():
    selected = face_listbox.curselection()
    if not selected:
        messagebox.showerror("Error", "Select a face to delete!")
        return

    selected_name = face_listbox.get(selected[0])

    # Remove the face from the dictionary
    del face_data[selected_name]

    # Save data to the file
    save_data()

    # Update the lists
    index = known_face_names.index(selected_name)
    known_face_encodings.pop(index)
    known_face_names.pop(index)
    known_face_params.pop(index)

    messagebox.showinfo("Success", f"Face {selected_name} deleted!")
    update_face_list()

# Function to update the face list
def update_face_list():
    selected_index = face_listbox.curselection()  # Save the selected item
    face_listbox.delete(0, "end")
    # Add known faces
    for name in known_face_names:
        face_listbox.insert("end", name)
    # Add unknown faces
    for face_id, data in unknown_faces.items():
        face_listbox.insert("end", data["name"])
    # Restore the selected item
    if selected_index:
        face_listbox.selection_set(selected_index[0])

# Load encodings from the file
known_face_encodings = []
known_face_names = []
known_face_params = []

for name, data in face_data.items():
    known_face_encodings.append(np.array(data["encoding"]))
    known_face_names.append(name)
    known_face_params.append(data["params"])

# Start the webcam
video_capture_index = int(input("Enter a video capture index: "))
cap = cv2.VideoCapture(video_capture_index)

# Dictionary to store temporary data about unknown faces
unknown_faces = {}  # {face_id: {"encoding": encoding, "name": "Unknown_X"}}
unknown_counter = 1  # Counter for unique identifiers

# Create the main window for the video stream
root = Tk()
root.title("Face Recognition")
root.withdraw()

# Create the window for the face list
list_window = Toplevel(root)
list_window.title("Face List")

# Face list
face_listbox = Listbox(list_window)
face_listbox.pack(padx=10, pady=10)

# Buttons for editing and deleting
Button(list_window, text="Edit", command=edit_face).pack(side="left", padx=10, pady=10)
Button(list_window, text="Delete", command=delete_face).pack(side="right", padx=10, pady=10)

# Update the face list
update_face_list()

# Variable to track changes in the face list
last_face_count = len(known_face_names) + len(unknown_faces)

while True:
    # Capture a frame from the webcam
    ret, frame = cap.read()
    if not ret:
        print("Error capturing frame!")
        break

    # Find faces in the frame
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    # Update the list of unknown faces
    unknown_faces = {}  # Clear the unknown faces dictionary
    unknown_counter = 1  # Reset the counter

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = None
        params = ""

        # If a match is found
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
            params = known_face_params[first_match_index]
        else:
            # If the face is unknown, add it to the dictionary
            face_id = f"Unknown_{unknown_counter}"
            unknown_counter += 1
            unknown_faces[face_id] = {"encoding": face_encoding, "name": face_id}
            name = face_id

        # Draw a rectangle around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Display the name and parameters
        label = f"{name} - {params}" if params else name
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # Display the frame
    cv2.imshow('Face Recognition', frame)

    # Update the face list if the number of faces has changed
    current_face_count = len(known_face_names) + len(unknown_faces)
    if current_face_count != last_face_count:
        update_face_list()
        last_face_count = current_face_count

    # Handle key presses
    key = cv2.waitKey(1)
    if key == ord('q'):  # Exit
        break
    elif key == ord('c'):  # Add a new face
        if unknown_faces:
            # Open the window to input data for the first unknown face
            face_id = list(unknown_faces.keys())[0]  # Take the first unknown face
            add_new_face(face_id, unknown_faces)

    # Update the GUI
    root.update()

# Release resources
cap.release()
cv2.destroyAllWindows()
root.destroy()