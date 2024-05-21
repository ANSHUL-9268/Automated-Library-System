import tkinter as tk
from tkinter import messagebox
import mysql.connector
from datetime import datetime, timedelta

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="intellib"
)
cursor = db.cursor()

class StudentPortal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Portal")
        self.geometry("400x300")

        self.label_enrollment = tk.Label(self, text="Enter Enrollment Number:")
        self.label_enrollment.pack(pady=5)
        self.entry_enrollment = tk.Entry(self)
        self.entry_enrollment.pack(pady=5)

        self.button_check_books_issued = tk.Button(self, text="Check Books Issued", command=self.check_books_issued)
        self.button_check_books_issued.pack(pady=5)

        self.button_check_deadlines = tk.Button(self, text="Check Deadlines", command=self.check_deadlines)
        self.button_check_deadlines.pack(pady=5)

        self.button_check_fine = tk.Button(self, text="Check Fine", command=self.check_fine)
        self.button_check_fine.pack(pady=5)


    def check_books_issued(self):
        enrollment_no = self.entry_enrollment.get()
        if enrollment_no:
            cursor.execute("SELECT book_issued, issue_date, return_date, fine FROM book_issue WHERE enrollment_no = %s", (enrollment_no,))
            results = cursor.fetchall()
            if results:
                messagebox.showinfo("Books Issued", "Books issued on your name:\n" + "\n".join([f"{row[0]} - Issue Date: {row[1]}, Return Date: {row[2]}, Fine: {row[3]}" for row in results]))
            else:
                messagebox.showinfo("No Books Issued", "No books issued on your name.")
        else:
            messagebox.showerror("Error", "Please enter enrollment number.")

    def check_deadlines(self):
        enrollment_no = self.entry_enrollment.get()
        if enrollment_no:
            cursor.execute("SELECT book_issued, return_date FROM book_issue WHERE enrollment_no = %s", (enrollment_no,))
            results = cursor.fetchall()
            if results:
                today = datetime.now().date()
                deadlines = [f"{row[0]} - Deadline: {row[1]}" for row in results if row[1] < today]
                if deadlines:
                    messagebox.showinfo("Deadlines Passed", "Deadlines passed for:\n" + "\n".join(deadlines))
                else:
                    messagebox.showinfo("No Deadlines Passed", "No deadlines passed for any books.")
            else:
                messagebox.showinfo("No Books Issued", "No books issued on your name.")
        else:
            messagebox.showerror("Error", "Please enter enrollment number.")

    def check_fine(self):
        enrollment_no = self.entry_enrollment.get()
        if enrollment_no:
            cursor.execute("SELECT SUM(fine) FROM book_issue WHERE enrollment_no = %s", (enrollment_no,))
            result = cursor.fetchone()
            if result[0]:
                messagebox.showinfo("Fine", f"Total fine to pay: {result[0]}")
            else:
                messagebox.showinfo("No Fine", "No fine to pay.")
        else:
            messagebox.showerror("Error", "Please enter enrollment number.")

    def check_book_availability(self):
        book_issued = self.entry_enrollment.get() 
        if book_issued:
            cursor.execute("SELECT status FROM book_issue WHERE book_issued = %s", (book_issued,))
            result = cursor.fetchone()
            if result:
                if result[0] == 'issued':
                    messagebox.showinfo("Book Availability", "Book is currently issued.")
                else:
                    messagebox.showinfo("Book Availability", "Book is available.")
            else:
                messagebox.showinfo("Book Availability", "Book not found in records.")
        else:
            messagebox.showerror("Error", "Please enter book ID.")

if __name__ == "__main__":
    student_portal = StudentPortal()
    student_portal.mainloop()
