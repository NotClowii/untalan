import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QComboBox, QLabel,
    QLineEdit, QHeaderView, QDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from Database_CAPSTEM import Database

db = Database()
STATUSES = ["Pending", "Processing", "Approved", "Rejected"]


class AdminPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAPSTEM - Admin Panel")
        self.resize(1000, 650)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tabs
        self.doc_tab = QWidget()
        self.checkup_tab = QWidget()
        self.complaint_tab = QWidget()
        self.schedule_tab = QWidget()
        self.analytics_tab = QWidget()
        self.users_tab = QWidget()

        self.tabs.addTab(self.doc_tab, "Documents")
        self.tabs.addTab(self.checkup_tab, "Checkups")
        self.tabs.addTab(self.complaint_tab, "Complaints")
        self.tabs.addTab(self.schedule_tab, "Free Checkup Schedules")
        self.tabs.addTab(self.analytics_tab, "Analytics")
        self.tabs.addTab(self.users_tab, "Users")

        self.init_doc_tab()
        self.init_checkup_tab()
        self.init_complaint_tab()
        self.init_schedule_tab()
        self.init_analytics_tab()
        self.init_users_tab()

        # Load data
        self.load_documents()
        self.load_checkups()
        self.load_complaints()
        self.load_schedules()
        self.load_users()

    def _send_notification(self, username, ntype, message):
        """Send a notification to user"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.execute(
                "INSERT INTO notifications (username, type, message, created_on) VALUES (%s, %s, %s, %s)",
                (username, ntype, message, now),
                commit=True
            )
            print(f" Notification sent to {username}: {message}")
        except Exception as e:
            print(f" Failed to send notification: {e}")

    def _update_status(self, table, row_id, status):
        """Update request status and notify user"""
        try:
            conn = db._conn()
            cur = conn.cursor(dictionary=True)

            if table == "documents":
                cur.execute("SELECT username, doc_type FROM documents WHERE id=%s", (row_id,))
                row = cur.fetchone()
                username, doc_type = row["username"], row["doc_type"]
                message = f" Your document request '{doc_type}' has been {status.lower()}."
                ntype = "document"

            elif table == "checkups":
                cur.execute("SELECT username, scheduled_date FROM checkups WHERE id=%s", (row_id,))
                row = cur.fetchone()
                username, date = row["username"], row["scheduled_date"]
                message = f" Your checkup for {date} has been {status.lower()}."
                ntype = "health"

            elif table == "complaints":
                cur.execute("SELECT username FROM complaints WHERE id=%s", (row_id,))
                row = cur.fetchone()
                username = row["username"]
                message = f" Your complaint has been {status.lower()}."
                ntype = "complaint"

            cur.execute(f"UPDATE {table} SET status=%s WHERE id=%s", (status, row_id))
            conn.commit()
            conn.close()

            self._send_notification(username, ntype, message)
            QMessageBox.information(self, "Updated", f"Status changed to {status} and user notified.")

            if table == "documents":
                self.load_documents()
            elif table == "checkups":
                self.load_checkups()
            elif table == "complaints":
                self.load_complaints()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update status: {e}")

    def init_doc_tab(self):
        layout = QVBoxLayout(self.doc_tab)
        self.doc_table = QTableWidget()
        self.doc_table.setColumnCount(6)
        self.doc_table.setHorizontalHeaderLabels(["ID", "Username", "Type", "Reason", "Status", "Requested On"])
        self.doc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.doc_table)

        btns = QHBoxLayout()
        self.doc_status = QComboBox()
        self.doc_status.addItems(STATUSES)
        update_btn = QPushButton("Update Status")
        update_btn.clicked.connect(self.update_doc_status)
        btns.addWidget(QLabel("Change status to:"))
        btns.addWidget(self.doc_status)
        btns.addWidget(update_btn)
        layout.addLayout(btns)

    def load_documents(self):
        rows = db.execute("SELECT id, username, doc_type, reason, status, requested_on FROM documents ORDER BY id DESC", fetchall=True)
        self.doc_table.setRowCount(len(rows or []))
        if rows:
            for i, r in enumerate(rows):
                for j, val in enumerate(r.values()):
                    self.doc_table.setItem(i, j, QTableWidgetItem(str(val)))

    def update_doc_status(self):
        row = self.doc_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Select a row first.")
            return
        rid = int(self.doc_table.item(row, 0).text())
        new_status = self.doc_status.currentText()
        self._update_status("documents", rid, new_status)

    def init_checkup_tab(self):
        layout = QVBoxLayout(self.checkup_tab)
        self.checkup_table = QTableWidget()
        self.checkup_table.setColumnCount(5)
        self.checkup_table.setHorizontalHeaderLabels(["ID", "Username", "Scheduled Date", "Requested On", "Status"])
        self.checkup_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.checkup_table)

        btns = QHBoxLayout()
        self.checkup_status = QComboBox()
        self.checkup_status.addItems(STATUSES)
        update_btn = QPushButton("Update Status")
        update_btn.clicked.connect(self.update_checkup_status)
        btns.addWidget(QLabel("Change status to:"))
        btns.addWidget(self.checkup_status)
        btns.addWidget(update_btn)
        layout.addLayout(btns)

    def load_checkups(self):
        rows = db.execute("SELECT id, username, scheduled_date, requested_on, status FROM checkups ORDER BY id DESC", fetchall=True)
        self.checkup_table.setRowCount(len(rows or []))
        if rows:
            for i, r in enumerate(rows):
                for j, val in enumerate(r.values()):
                    self.checkup_table.setItem(i, j, QTableWidgetItem(str(val)))

    def update_checkup_status(self):
        row = self.checkup_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Select a row first.")
            return
        rid = int(self.checkup_table.item(row, 0).text())
        new_status = self.checkup_status.currentText()
        self._update_status("checkups", rid, new_status)

    def init_complaint_tab(self):
        layout = QVBoxLayout(self.complaint_tab)
        self.complaint_table = QTableWidget()
        self.complaint_table.setColumnCount(6)
        self.complaint_table.setHorizontalHeaderLabels(["ID", "Username", "Complaint", "Photo", "Submitted On", "Status"])
        self.complaint_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.complaint_table)

        btns = QHBoxLayout()
        self.complaint_status = QComboBox()
        self.complaint_status.addItems(STATUSES)
        update_btn = QPushButton("Update Status")
        update_btn.clicked.connect(self.update_complaint_status)
        view_photo_btn = QPushButton("View Photo")
        view_photo_btn.clicked.connect(self.view_complaint_photo)
        btns.addWidget(QLabel("Change status to:"))
        btns.addWidget(self.complaint_status)
        btns.addWidget(update_btn)
        btns.addWidget(view_photo_btn)
        layout.addLayout(btns)

    def load_complaints(self):
        rows = db.execute("SELECT id, username, complaint, photo, submitted_on, status FROM complaints ORDER BY id DESC", fetchall=True)
        self.complaint_table.setRowCount(len(rows or []))
        if rows:
            for i, r in enumerate(rows):
                for j, val in enumerate(r.values()):
                    self.complaint_table.setItem(i, j, QTableWidgetItem(str(val)))

    def update_complaint_status(self):
        row = self.complaint_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Select a row first.")
            return
        rid = int(self.complaint_table.item(row, 0).text())
        new_status = self.complaint_status.currentText()
        self._update_status("complaints", rid, new_status)

    def view_complaint_photo(self):
        row = self.complaint_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Please select a complaint row.")
            return
        photo_path = self.complaint_table.item(row, 3).text()
        if not photo_path or photo_path.lower() in ['none', 'null', '']:
            QMessageBox.information(self, "No Photo", "No photo attached to this complaint.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Complaint Photo")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)

        image_label = QLabel()
        pixmap = QPixmap(photo_path)
        if pixmap.isNull():
            image_label.setText(f"Could not load image:\n{photo_path}")
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            scaled_pixmap = pixmap.scaled(780, 580, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def init_schedule_tab(self):
        layout = QVBoxLayout(self.schedule_tab)
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(2)
        self.schedule_table.setHorizontalHeaderLabels(["ID", "Scheduled Date"])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.schedule_table)

        row = QHBoxLayout()
        self.new_date = QLineEdit()
        self.new_date.setPlaceholderText("YYYY-MM-DD")
        add_btn = QPushButton("Add Free Checkup Schedule")
        add_btn.clicked.connect(self.add_schedule)
        row.addWidget(self.new_date)
        row.addWidget(add_btn)
        layout.addLayout(row)

    def load_schedules(self):
        rows = db.execute("SELECT id, scheduled_date FROM checkups WHERE username='FREE' ORDER BY id DESC", fetchall=True)
        self.schedule_table.setRowCount(len(rows or []))
        if rows:
            for i, r in enumerate(rows):
                self.schedule_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
                self.schedule_table.setItem(i, 1, QTableWidgetItem(str(r["scheduled_date"])))

    def add_schedule(self):
        date_str = self.new_date.text().strip()
        if not date_str:
            QMessageBox.warning(self, "Missing", "Enter a date in YYYY-MM-DD format.")
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "INSERT INTO checkups (username, scheduled_date, requested_on, status) VALUES (%s, %s, %s, %s)",
            ("FREE", date_str, now, "Approved"),
            commit=True
        )
        QMessageBox.information(self, "Added", f"Free checkup schedule added for {date_str}")
        self.load_schedules()
        self.new_date.clear()

    def init_analytics_tab(self):
        layout = QVBoxLayout(self.analytics_tab)
        self.user_count_label = QLabel()
        layout.addWidget(self.user_count_label)
        self.figure = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.load_analytics()

    def load_analytics(self):
        conn = db._conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        self.user_count_label.setText(f"👥 Total Users: {user_count}")

        cur.execute("SELECT status, COUNT(*) FROM documents GROUP BY status")
        doc_statuses = cur.fetchall()
        cur.execute("SELECT status, COUNT(*) FROM complaints GROUP BY status")
        complaint_statuses = cur.fetchall()
        conn.close()

        self.figure.clear()
        if doc_statuses:
            ax1 = self.figure.add_subplot(121)
            labels, counts = zip(*doc_statuses)
            ax1.pie(counts, labels=labels, autopct='%1.1f%%')
            ax1.set_title("Documents Status")
        if complaint_statuses:
            ax2 = self.figure.add_subplot(122)
            labels, counts = zip(*complaint_statuses)
            ax2.bar(labels, counts)
            ax2.set_title("Complaints Status")
        self.canvas.draw()

    def init_users_tab(self):
        layout = QVBoxLayout(self.users_tab)
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(8)
        self.users_table.setHorizontalHeaderLabels(["ID", "Username", "Full Name", "Email", "Phone", "Address", "Status", "Warnings"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.users_table)

        btns = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Users")
        refresh_btn.clicked.connect(self.load_users)
        ban_btn = QPushButton("Toggle Ban")
        ban_btn.clicked.connect(self.toggle_user_ban)
        warn_btn = QPushButton("Add Warning")
        warn_btn.clicked.connect(self.give_user_warning)
        btns.addWidget(refresh_btn)
        btns.addWidget(ban_btn)
        btns.addWidget(warn_btn)
        layout.addLayout(btns)

    def load_users(self):
        rows = db.execute(
            "SELECT id, username, fullname, email, phone, address, COALESCE(status,'Active') as status, COALESCE(warnings,0) as warnings FROM users ORDER BY id DESC",
            fetchall=True
        )
        self.users_table.setRowCount(len(rows or []))
        if rows:
            for i, r in enumerate(rows):
                for j, val in enumerate(r.values()):
                    self.users_table.setItem(i, j, QTableWidgetItem(str(val)))

    def toggle_user_ban(self):
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Select a user first.")
            return
        uid = int(self.users_table.item(row, 0).text())
        username = self.users_table.item(row, 1).text()
        current_status = self.users_table.item(row, 6).text()
        new_status = "Banned" if current_status != "Banned" else "Active"
        db.execute("UPDATE users SET status=%s WHERE id=%s", (new_status, uid), commit=True)

        if new_status == "Banned":
            msg = "⚠️ Your account has been banned by admin."
        else:
            msg = "✅ Your account has been unbanned."
        self._send_notification(username, "account", msg)
        QMessageBox.information(self, "Updated", f"User status changed to {new_status}.")
        self.load_users()

    def give_user_warning(self):
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Select a user first.")
            return
        uid = int(self.users_table.item(row, 0).text())
        username = self.users_table.item(row, 1).text()
        user = db.execute("SELECT warnings FROM users WHERE id=%s", (uid,), fetchone=True)
        current = user["warnings"] if user else 0
        new_warnings = current + 1
        db.execute("UPDATE users SET warnings=%s WHERE id=%s", (new_warnings, uid), commit=True)
        msg = f"⚠️ Warning #{new_warnings}: Please follow community guidelines."
        self._send_notification(username, "warning", msg)
        QMessageBox.information(self, "Warning Added", f"Warning added to {username}. Total: {new_warnings}")
        self.load_users()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    panel = AdminPanel()
    panel.show()
    sys.exit(app.exec())
