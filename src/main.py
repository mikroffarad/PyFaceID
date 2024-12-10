import cv2
import face_recognition
import os
import numpy as np

class FaceRecognition:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_known_faces()

    def load_known_faces(self):
        # Create directory for known faces if it doesn't exist
        known_faces_dir = 'known_faces'
        if not os.path.exists(known_faces_dir):
            os.makedirs(known_faces_dir)

        # Load previously saved faces
        for filename in os.listdir(known_faces_dir):
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                image_path = os.path.join(known_faces_dir, filename)
                face_image = face_recognition.load_image_file(image_path)

                # Get face encoding
                face_encoding = face_recognition.face_encodings(face_image)

                if face_encoding:
                    # Extract name from filename
                    name = os.path.splitext(filename)[0].replace('face_', '')

                    self.known_face_encodings.append(face_encoding[0])
                    self.known_face_names.append(name)

    def capture_and_save_face(self):
        # Initialize video capture
        video_capture = cv2.VideoCapture(0)

        while True:
            # Capture frame
            ret, frame = video_capture.read()

            # Find faces in the frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            # Draw rectangles around faces and recognize
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Draw rectangle around face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

                # Recognize face
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "Unknown"

                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.known_face_names[first_match_index]

                # Add name near rectangle
                cv2.putText(frame, name, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Add instructions to the screen
            instructions = "Press 'c' to capture face, 'q' to quit"
            cv2.putText(frame, instructions, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Show frame
            cv2.imshow('Face Recognition', frame)

            # Process key presses
            key = cv2.waitKey(1) & 0xFF

            # Press 'c' to capture face
            if key == ord('c') and face_locations:
                # Take the first detected face
                top, right, bottom, left = face_locations[0]
                face_image = frame[top:bottom, left:right]

                # Prompt for user name
                name = input("Enter a name for this face: ").strip()

                if name:
                    # Generate filename
                    filename = f'known_faces/{name}.jpg'

                    # Save face image
                    cv2.imwrite(filename, face_image)

                    # Add face to database
                    face_encoding = face_recognition.face_encodings(face_image)[0]
                    self.known_face_encodings.append(face_encoding)
                    self.known_face_names.append(name)

                    print(f"Face for {name} saved")

            # Quit on 'q' press
            elif key == ord('q'):
                break

        # Release resources
        video_capture.release()
        cv2.destroyAllWindows()

# Run the function
if __name__ == "__main__":
    face_rec = FaceRecognition()
    face_rec.capture_and_save_face()
