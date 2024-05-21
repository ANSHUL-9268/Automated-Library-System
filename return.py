import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import datetime
import os
import pytesseract
import pandas as pd
from pyzbar.pyzbar import decode
import mysql.connector
from datetime import timedelta


current_time = datetime.datetime.now()

manual_enrollment_number = None

scanned_barcode = None
detected_enrollment_number = None 

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


ID_CARD_IMAGE_DIR = "ID_card_image"
BOOK_BARCODE_IMAGE_DIR = "book_barcode_image"

for dir_path in [ID_CARD_IMAGE_DIR, BOOK_BARCODE_IMAGE_DIR]:
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)


def detect_enrollment_number(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)

    start = text.find("Enroll No.")
    enroll_no = None

    if start != -1:
        end = text.find("\n", start)
        enroll_no = text[start + 11:end].strip()
        return enroll_no
    return None

def save_enrollment_number(enroll_no):
    csv_path = "enrollment_numbers.csv"
    try:
        df_existing = pd.read_csv(csv_path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df_existing = pd.DataFrame(columns=["Enrollment Number"])

    if enroll_no not in df_existing["Enrollment Number"].values:
        df_new = pd.DataFrame([[enroll_no]], columns=["Enrollment Number"])
        df_existing = pd.concat([df_existing, df_new], ignore_index=True)
        df_existing.to_csv(csv_path, index=False)
        return True
    return False

def detect_enrollment_number_from_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)

    start = text.find("Enroll No.")
    enroll_no = None

    if start != -1:
        end = text.find("\n", start)
        enroll_no = text[start + 11:end].strip()
        return enroll_no
    return None

def decode_barcode(image_path):
    image = cv2.imread(image_path)
    decoded_objects = decode(image)

    if decoded_objects:
        barcode_data = decoded_objects[0].data.decode("utf-8")
        return barcode_data
    return None

def decode_barcode_from_frame(frame):
    decoded_objects = decode(frame)

    if decoded_objects:
        barcode_data = decoded_objects[0].data.decode("utf-8")
        return barcode_data
    return None

def capture_image(image_type):
    global detected_enrollment_number  

    cap = None
    try:
        
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            raise Exception("Unable to open default camera (index 0).")

        capture_window = tk.Toplevel()
        capture_window.title("Camera Capture")
        capture_window.geometry("640x480")

        def update_frame():
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)
                panel.configure(image=photo)
                panel.image = photo

                if image_type == "ID_Card":
                    global detected_enrollment_number
                    detected_enrollment_number = detect_enrollment_number_from_frame(frame)
                    if detected_enrollment_number:
                        if save_enrollment_number(detected_enrollment_number):
                            messagebox.showinfo("Success", f"Enrollment number {detected_enrollment_number} saved!")
                        else:
                            messagebox.showinfo("Info", f"Enrollment number {detected_enrollment_number} already exists.")

                elif image_type == "Book_Barcode":
                    global scanned_barcode
                    scanned_barcode = decode_barcode_from_frame(frame)
                    if scanned_barcode:
                        books = {
                            '1234567891026': {
                                'title': 'Machine Learning Book',
                                'author': 'John Doe',
                                'year': '2021'
                            },
                            'BOOK1-12345':{
                                'title': 'Machine Learning Book2',
                                'author': 'XYZ',
                                'year': '2023'
                            },
                            'BOOK1-123':{
                                'title': 'Machine Learning Book3',
                                'author': 'ABC',
                                'year': '2024'
                            }
                        }
                        book_info = books.get(scanned_barcode, None)
                        if book_info:
                            book_details = f"Title: {book_info['title']}\nAuthor: {book_info['author']}\nYear: {book_info['year']}"
                            messagebox.showinfo("Book Info", book_details)
                        else:
                            messagebox.showerror("Error", f"No book found for barcode {scanned_barcode}")

                capture_window.after(10, update_frame)

        panel = tk.Label(capture_window)
        panel.pack()

        update_frame()

    except Exception as e:
        if cap:
            cap.release()
        messagebox.showerror("Error", f"Error accessing camera: {e}")

def issue_book():
    issue_window = tk.Toplevel()
    issue_window.title("Issue Book")
    issue_window.geometry("300x200")

    id_card_button = tk.Button(issue_window, text="ID Card", command=lambda: capture_image("ID_Card"))
    id_card_button.pack(pady=10)

    barcode_button = tk.Button(issue_window, text="Book Barcode", command=lambda: capture_image("Book_Barcode"))
    barcode_button.pack(pady=10)

    manual_enrollment_label = tk.Label(issue_window, text="Manual Enrollment")
    manual_enrollment_label.pack(pady=5)

    manual_enrollment_entry = tk.Entry(issue_window)
    manual_enrollment_entry.pack(pady=5)

    def issue_book_internal():
        global manual_enrollment_number
        manual_enrollment_number = manual_enrollment_entry.get()
        issue_date = datetime.datetime.now().date()
        return_date = issue_date + timedelta(days=7)

        
        enrollment_number = detected_enrollment_number if detected_enrollment_number else manual_enrollment_number

        cursor.execute("SELECT first_name, last_name, semester FROM student_record WHERE enrollment_no = %s", (enrollment_number,))
        result = cursor.fetchone()
        if result:
            issuer_first_name, issuer_last_name, issuer_semester = result
            query = "INSERT INTO book_issue (book_issued, issue_date, return_date, enrollment_no, issuer_first_name, issuer_last_name, issuer_semester) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            values = (scanned_barcode, issue_date, return_date, enrollment_number, issuer_first_name, issuer_last_name, issuer_semester)
            cursor.execute(query, values)
            db.commit()
            messagebox.showinfo("Success", "Book issued successfully.")
        else:
            messagebox.showerror("Error", "Student record not found.")

    issue_button = tk.Button(issue_window, text="Issue Book", command=issue_book_internal)
    issue_button.pack(pady=10)

def return_book():
    return_window = tk.Toplevel()
    return_window.title("Return Book")
    return_window.geometry("300x200")

    barcode_button = tk.Button(return_window, text="Book Barcode", command=lambda: capture_image("Book_Barcode"))
    barcode_button.pack(pady=10)

    manual_enrollment_label = tk.Label(return_window, text="Manual Enrollment")
    manual_enrollment_label.pack(pady=5)

    manual_enrollment_entry = tk.Entry(return_window)
    manual_enrollment_entry.pack(pady=5)

    def return_book_internal():
        global manual_enrollment_number
        manual_enrollment_number = manual_enrollment_entry.get()

        cursor.execute("SELECT issue_date, return_date FROM book_issue WHERE book_issued = %s AND enrollment_no = %s", (scanned_barcode, manual_enrollment_number))
        result = cursor.fetchone()
        if result:
            issue_date, return_date = result
            today = datetime.datetime.now().date()
            if today > return_date:
                days_late = (today - return_date).days
                fine = days_late * 0.5
                cursor.execute("UPDATE book_issue SET fine = %s WHERE book_issued = %s AND enrollment_no = %s", (fine, scanned_barcode, manual_enrollment_number))
                db.commit()
                messagebox.showinfo("Success", f"Book returned with a fine of ${fine:.2f}")
            else:
                cursor.execute("DELETE FROM book_issue WHERE book_issued = %s AND enrollment_no = %s", (scanned_barcode, manual_enrollment_number))
                db.commit()
                messagebox.showinfo("Success", "Book returned successfully.")
        else:
            messagebox.showerror("Error", "Book not issued to this student.")

    return_button = tk.Button(return_window, text="Return Book", command=return_book_internal)
    return_button.pack(pady=10)


app = tk.Tk()
app.title("IntelliLib - Intelligent Library")
app.geometry("300x200")


issue_button = tk.Button(app, text="Issue Book", command=issue_book)
issue_button.pack(pady=10)

return_button = tk.Button(app, text="Return Book", command=return_book)
return_button.pack(pady=10)


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="intellib"
)
cursor = db.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_record (
        enrollment_no VARCHAR(20) PRIMARY KEY,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        semester INT,
        contact_details VARCHAR(100)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS book_issue (
        book_id INT AUTO_INCREMENT PRIMARY KEY,
        book_issued VARCHAR(100),
        issue_date DATE,
        return_date DATE,
        enrollment_no VARCHAR(20),
        issuer_first_name VARCHAR(50),
        issuer_last_name VARCHAR(50),
        issuer_semester INT,
        status VARCHAR(10),
        fine DECIMAL(5,2) DEFAULT 0,
        FOREIGN KEY (enrollment_no) REFERENCES student_record(enrollment_no)
    )
""")

app.mainloop()
