import cv2
import face_recognition
import os
import numpy as np
import tkinter as tk
from tkinter import simpledialog

def capture_and_recognize_faces():
    # Initialize the webcam
    video_capture = cv2.VideoCapture(2)

    # Create directory for saving faces if it doesn't exist
    if not os.path.exists('known_faces'):
        os.makedirs('known_faces')

    known_face_encodings = []
    known_face_names = []

    # Load saved faces
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
            print(f"Could not find a face in the image {filename}. Please check the file.")

    # Function to get the user's name through a dialog box
    def get_user_name():
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        user_name = simpledialog.askstring("Enter Name", "Please enter your name:")
        root.destroy()  # Close the window after input
        return user_name

    while True:
        # Capture a frame
        ret, frame = video_capture.read()

        # Detect faces in the frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Recognize faces
        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            face_names.append(name)

        # Draw rectangles and labels
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Add instructions to the screen
        instructions = "Press 'c' to capture face, 'q' to quit"
        cv2.putText(frame, instructions, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Show the frame
        cv2.imshow('Face Recognition', frame)

        # Handle key presses
        key = cv2.waitKey(1) & 0xFF

        # Press 'c' to capture a face
        if key == ord('c'):
            user_name = get_user_name()
            if user_name:
                if face_locations:
                    top, right, bottom, left = face_locations[0]
                    face_image = frame[top:bottom, left:right]

                    # Save the face image
                    filename = f'known_faces/{user_name}.jpg'
                    cv2.imwrite(filename, face_image)

                    # Update the list of saved faces
                    image = face_recognition.load_image_file(filename)
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        encoding = encodings[0]
                        known_face_encodings.append(encoding)
                        known_face_names.append(user_name)
                        print(f"Face saved as {filename}")
                    else:
                        print(f"Could not find a face in the image {filename}. Please check the image quality.")
                        os.remove(filename)  # Remove the invalid image

                    # Display a message on the screen
                    cv2.putText(frame, "Face Captured!", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.imshow('Face Recognition', frame)
                    cv2.waitKey(1000)  # Display the message for a second

        # Exit on pressing 'q'
        elif key == ord('q'):
            break

    # Release resources
    video_capture.release()
    cv2.destroyAllWindows()

# Run the function
if __name__ == "__main__":
    capture_and_recognize_faces()
