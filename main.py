import sys
import os
import mysql.connector

from datetime import datetime
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QStackedWidget, QComboBox, QMessageBox,
    QCalendarWidget, QFileDialog, QTableWidget, QTableWidgetItem, QTabWidget,
    QInputDialog, QPlainTextEdit, QHeaderView
)

from Database_CAPSTEM import Database

LOGO_FILE = r"C:\Users\nicol\Downloads\blue.png"

def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")




class UserManager:
    def __init__(self, db):
        self.db = db
        self.current_user = None

    def reload(self):
        pass

    def save(self):
        return True

    def register(self, username, password, email, phone, fullname, address):
        if not username or not password or not fullname or not address:
            return False, "Username, password, full name and address are required."
        try:
            self.db.execute(
                "INSERT INTO users (username, password, email, phone, fullname, address) VALUES (%s, %s, %s, %s, %s, %s)",
                (username, password, email, phone, fullname, address),
                commit=True
            )
            row = self.db.execute("SELECT id FROM users WHERE username = %s", (username,), fetchone=True)
            return True, row['id'] if row else True
        except mysql.connector.IntegrityError:
            return False, "Username already exists."
        except Exception as e:
            return False, f"Failed to register: {e}"

    def login(self, username, password):
        try:
            row = self.db.execute(
                "SELECT id, username, password, email, phone, fullname, address, COALESCE(status, 'Active') as status, COALESCE(warnings, 0) as warnings FROM users WHERE LOWER(username) = LOWER(%s)",
                (username,), fetchone=True
            )
            if row and row['password'] == password:
                self.current_user = {
                    "id": row['id'],
                    "username": row['username'],
                    "password": row['password'],
                    "email": row['email'],
                    "phone": row['phone'],
                    "fullname": row['fullname'],
                    "address": row['address'],
                    "status": row['status'],
                    "warnings": row['warnings']
                }
                return True
            return False
        except Exception as e:
            print(f"Error in login: {e}")
            return False

    def find_by_username(self, username):
        try:
            row = self.db.execute(
                "SELECT id, username, password, email, phone, fullname, address, COALESCE(status, 'Active') as status, COALESCE(warnings, 0) as warnings FROM users WHERE LOWER(username) = LOWER(%s)",
                (username,), fetchone=True
            )
            if not row:
                return None
            return {
                "id": row['id'],
                "username": row['username'],
                "password": row['password'],
                "email": row['email'],
                "phone": row['phone'],
                "fullname": row['fullname'],
                "address": row['address'],
                "status": row['status'],
                "warnings": row['warnings']
            }
        except Exception as e:
            print(f"find_by_username error: {e}")
            return None




class RequestManager:
    def __init__(self, db, user_manager):
        self.db = db
        self.um = user_manager

    def reload_data(self):
        pass

    def save(self):
        return True

    # Documents
    def submit_document(self, username, doc_type, reason):
        try:
            now = now_ts()
            result = self.db.execute(
                "INSERT INTO documents (username, doc_type, reason, status, requested_on) VALUES (%s, %s, %s, %s, %s)",
                (username, doc_type, reason, "Waiting", now),
                commit=True
            )
            self._notify(username, "document", f"Document request '{doc_type}' submitted (Waiting).")
            doc_id = result[0] if result else None
            return {"id": doc_id, "username": username, "doc_type": doc_type, "reason": reason, "status": "Waiting", "requested_on": now}
        except Exception as e:
            print(f"Error in submit_document: {e}")
            return None

    def list_documents_for_user(self, username):
        try:
            rows = self.db.execute(
                "SELECT id, username, doc_type, reason, status, requested_on FROM documents WHERE LOWER(username) = LOWER(%s) ORDER BY id",
                (username,), fetchall=True
            )
            return [{"id": r['id'], "username": r['username'], "doc_type": r['doc_type'], "reason": r['reason'], "status": r['status'], "requested_on": str(r['requested_on'])} for r in rows] if rows else []
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []

    # Checkups
    def submit_checkup(self, username, date_str):
        try:
            now = now_ts()
            result = self.db.execute(
                "INSERT INTO checkups (username, scheduled_date, requested_on, status) VALUES (%s, %s, %s, %s)",
                (username, date_str, now, "Waiting"),
                commit=True
            )
            self._notify(username, "health", f"Checkup requested for {date_str} (Waiting).")
            checkup_id = result[0] if result else None
            return {"id": checkup_id, "username": username, "scheduled_date": date_str, "requested_on": now, "status": "Waiting"}
        except Exception as e:
            print(f"Error in submit_checkup: {e}")
            return None

    def list_checkups_for_user(self, username):
        try:
            rows = self.db.execute(
                "SELECT id, username, scheduled_date, requested_on, status FROM checkups WHERE LOWER(username) = LOWER(%s) ORDER BY id",
                (username,), fetchall=True
            )
            return [{"id": r['id'], "username": r['username'], "scheduled_date": str(r['scheduled_date']), "requested_on": str(r['requested_on']), "status": r['status']} for r in rows] if rows else []
        except Exception as e:
            print(f"Error listing checkups: {e}")
            return []

    # Complaints
    def submit_complaint(self, username, complaint_text, photo_path=None):
        try:
            now = now_ts()
            result = self.db.execute(
                "INSERT INTO complaints (username, complaint, photo, submitted_on, status) VALUES (%s, %s, %s, %s, %s)",
                (username, complaint_text, photo_path or "", now, "Waiting"),
                commit=True
            )
            self._notify(username, "complaint", "Complaint submitted (Waiting).")
            complaint_id = result[0] if result else None
            return {"id": complaint_id, "username": username, "complaint": complaint_text, "photo": photo_path or "", "submitted_on": now, "status": "Waiting"}
        except Exception as e:
            print(f"Error in submit_complaint: {e}")
            return None

    def list_complaints_for_user(self, username):
        try:
            rows = self.db.execute(
                "SELECT id, username, complaint, photo, submitted_on, status FROM complaints WHERE LOWER(username) = LOWER(%s) ORDER BY id",
                (username,), fetchall=True
            )
            return [{"id": r['id'], "username": r['username'], "complaint": r['complaint'], "photo": r['photo'], "submitted_on": str(r['submitted_on']), "status": r['status']} for r in rows] if rows else []
        except Exception as e:
            print(f"Error listing complaints: {e}")
            return []

    # Notifications
    def _notify(self, username, ntype, message):
        try:
            now = now_ts()
            self.db.execute(
                "INSERT INTO notifications (username, type, message, created_on) VALUES (%s, %s, %s, %s)",
                (username, ntype, message, now),
                commit=True
            )
        except Exception as e:
            print(f"Error in _notify: {e}")

    def list_notifications_for_user(self, username):
        try:
            rows = self.db.execute(
                "SELECT id, username, type, message, created_on FROM notifications WHERE LOWER(username) = LOWER(%s) ORDER BY id",
                (username,), fetchall=True
            )
            return [{"id": r['id'], "username": r['username'], "type": r['type'], "message": r['message'], "created_on": str(r['created_on'])} for r in rows] if rows else []
        except Exception as e:
            print(f"Error listing notifications: {e}")
            return []


CARD_STYLE = """
QFrame.card {
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 #FFFFFF, stop:1 #083a9a);
  border-radius: 14px;
  padding: 12px;
}
QLabel.cardTitle { color: white; font-weight: bold; font-size: 16px; }
QLabel.cardText { color: #dbeafe; font-size: 11px; }
QPushButton.cardBtn {
  background-color: #0b5ed7;
  color: white;
  border-radius: 10px;
  padding: 6px 12px;
}
QPushButton.cardBtn:hover { background-color: #083a9a; }
"""

APP_STYLE = """
QWidget { 
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    stop:0 #1861d6, stop:1 #083a9a); 
    color: white; 
    font-family: Arial; 
    font-size: 14px;
}
QLabel#mainTitle { 
    font-size: 28px; 
    font-weight: bold; 
    color: #e6f0ff; 
}
QLabel#subtitle { 
    color: #cfe6ff; 
    font-size: 12px; 
}
QPushButton { 
    background-color: #2b6bff; 
    color: white; 
    border-radius: 8px; 
    padding: 8px 16px; 
    font-size: 14px;
}
QPushButton:hover { 
    background-color: #1849b8; 
}
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox { 
    background: #ffffff; 
    color: #052043; 
    border-radius: 8px; 
    padding: 8px; 
    border: 1px solid #d1d5db;
    font-size: 14px;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus { 
    border: 1px solid #2b6bff;
}
QTableWidget { 
    background: #e6f0ff; 
    color: #052043; 
    border-radius: 8px;
}
QTableWidget::item { 
    padding: 8px;
}
"""

class LoginScreen(QWidget):
    def __init__(self, stack: QStackedWidget, um: UserManager, rm: RequestManager):
        super().__init__()
        self.stack = stack
        self.um = um
        self.rm = rm
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Logo
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label = QLabel()
        logo_label.setFixedSize(200, 100)
        if os.path.exists(LOGO_FILE):
            pix = QPixmap(LOGO_FILE)
            pix = pix.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pix)
        else:
            logo_label.setText("Logo not found")
            logo_label.setStyleSheet("color: #e6f0ff; font-size: 12px;")
        logo_layout.addWidget(logo_label)
        layout.addWidget(logo_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title and subtitle
        title = QLabel("Welcome Back")
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("Log in to access CAPSTEM Barangay Services")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Card for inputs
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        # Input fields
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)

        # Login button
        btn = QPushButton("Log In")
        btn.clicked.connect(self.handle_login)
        card_layout.addWidget(btn)

        # Admin login button
        admin_btn = QPushButton("Admin Login")
        admin_btn.setStyleSheet("""
            background-color: #ff5555;
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
        """)
        admin_btn.clicked.connect(self.handle_admin_login)
        card_layout.addWidget(admin_btn)

        # Signup link
        switch = QPushButton("Don't have an account? Sign Up")
        switch.setFlat(True)
        switch.setStyleSheet("""
            color: #ffffff;
            text-decoration: underline;
            font-size: 12px;
        """)
        switch.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        card_layout.addWidget(switch, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Missing", "Enter username and password.")
            return

        try:
            user = self.um.find_by_username(username)

            if not user:
                QMessageBox.warning(self, "Login Failed", "Wrong username or password.")
                return

            user_status = user.get('status', 'Active')
            if user_status == 'Banned':
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Account Banned")
                msg.setText(" Your account has been banned.")
                msg.setInformativeText(
                    "You cannot log in because your account has been suspended by the administrator.\n\n"
                    "Please contact the barangay office for more information or to appeal this decision."
                )
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                return

            ok = self.um.login(username, password)
            if ok:
                warnings = user.get('warnings', 0)
                if warnings > 0:
                    warning_msg = QMessageBox(self)
                    warning_msg.setIcon(QMessageBox.Icon.Warning)
                    warning_msg.setWindowTitle("Account Warning")
                    warning_msg.setText(f" You have {warnings} warning(s) on your account.")
                    warning_msg.setInformativeText(
                        "Please follow community guidelines to avoid account suspension.\n"
                        "Check your notifications for more details."
                    )
                    warning_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                    warning_msg.exec()

                QMessageBox.information(self, "Welcome", f"Welcome, {self.um.current_user['fullname']}!")
                try:
                    self.stack.widget(2).refresh_user()
                except Exception:
                    pass
                try:
                    comp_page = self.stack.widget(5)
                    if hasattr(comp_page, 'fullname'):
                        comp_page.fullname.setText(self.um.current_user['fullname'])
                except Exception:
                    pass
                self.stack.setCurrentIndex(2)
            else:
                QMessageBox.warning(self, "Login Failed", "Wrong username or password.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")

    def handle_admin_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if username == "admin" and password == "capstem123":
            QMessageBox.information(self, "Admin Login", "Welcome, Admin!")
            try:
                from ADMIN_CAPSTEM import AdminPanel
                self.admin_panel = AdminPanel()
                self.admin_panel.show()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open admin panel: {str(e)}")
        else:
            QMessageBox.warning(self, "Login Failed", "Wrong admin credentials.")


class SignupScreen(QWidget):
    def __init__(self, stack: QStackedWidget, um: UserManager):
        super().__init__()
        self.stack = stack
        self.um = um
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label = QLabel()
        logo_label.setFixedSize(200, 100)
        if os.path.exists(LOGO_FILE):
            pix = QPixmap(LOGO_FILE)
            pix = pix.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pix)
        else:
            logo_label.setText("Logo not found")
            logo_label.setStyleSheet("color: #e6f0ff; font-size: 12px;")
        logo_layout.addWidget(logo_label)
        layout.addWidget(logo_container, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Create Your Account")
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("Sign up to access CAPSTEM Barangay Services")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        self.fullname = QLineEdit()
        self.fullname.setPlaceholderText("Full name (e.g. Justin Nabunturan)")
        self.address = QLineEdit()
        self.address.setPlaceholderText("Address (e.g. Brgy. X, City Y)")
        self.username = QLineEdit()
        self.username.setPlaceholderText("Choose username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Choose password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Phone (e.g. +639...)")

        card_layout.addWidget(self.fullname)
        card_layout.addWidget(self.address)
        card_layout.addWidget(self.username)
        card_layout.addWidget(self.password)
        card_layout.addWidget(self.email)
        card_layout.addWidget(self.phone)

        # Buttons
        row = QHBoxLayout()
        signup_btn = QPushButton("Sign Up")
        signup_btn.clicked.connect(self.do_signup)
        back_btn = QPushButton("Back to Login")
        back_btn.setStyleSheet("""
            background-color: transparent;
            color: #ffffff;
            border: 1px solid #ffffff;
            border-radius: 40px;
            padding: 10px 40px;
        """)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        row.addWidget(signup_btn)
        row.addWidget(back_btn)
        card_layout.addLayout(row)

        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def do_signup(self):
        fullname = self.fullname.text().strip()
        address = self.address.text().strip()
        u = self.username.text().strip()
        p = self.password.text().strip()
        e = self.email.text().strip()
        ph = self.phone.text().strip()

        if not fullname or not address or not u or not p or not e or not ph:
            QMessageBox.warning(self, "Missing", "Fill all fields.")
            return

        try:
            ok, res = self.um.register(u, p, e, ph, fullname, address)
            if ok:
                QMessageBox.information(self, "Created", f"Account created. Your ID: #000{res}")
                self.stack.setCurrentIndex(0)
            else:
                QMessageBox.warning(self, "Error", res)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Registration failed: {str(e)}")

class DashboardScreen(QWidget):
    def __init__(self, stack: QStackedWidget, um: UserManager, rm: RequestManager):
        super().__init__()
        self.stack = stack
        self.um = um
        self.rm = rm
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(18)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        titles_layout = QVBoxLayout()
        titles_layout.setSpacing(5)
        self.title_lbl = QLabel("WELCOME TO CAPSTEM")
        self.title_lbl.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        titles_layout.addWidget(self.title_lbl)

        self.subtitle_lbl = QLabel("Fast, reliable and transparent online barangay services")
        self.subtitle_lbl.setFont(QFont("Arial", 14))
        self.subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        titles_layout.addWidget(self.subtitle_lbl)

        top_layout.addLayout(titles_layout, stretch=1)

        # Right side: dedicated logo space
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(200, 200)
        pix = QPixmap(r"C:\\Users\\nicol\\Downloads\\blue.png")
        if not pix.isNull():
            pix = pix.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText("Logo not found")
            self.logo_label.setStyleSheet("color: #e6f0ff; font-size: 12px;")

        logo_layout.addWidget(self.logo_label)
        top_layout.addWidget(logo_container)

        main_layout.addLayout(top_layout)

        # Cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        def make_card(title_text, lines, btn_text, slot):
            card = QFrame()
            card.setObjectName("card")
            card.setFixedSize(240, 160)
            v_layout = QVBoxLayout(card)
            v_layout.setSpacing(4)
            v_layout.setContentsMargins(20, 20, 20, 20)

            lbl = QLabel(title_text)
            lbl.setObjectName("cardTitle")
            lbl.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            v_layout.addWidget(lbl)

            for line in lines:
                l = QLabel(line)
                l.setObjectName("cardText")
                v_layout.addWidget(l)

            v_layout.addStretch()
            btn = QPushButton(btn_text)
            btn.setObjectName("cardBtn")
            btn.clicked.connect(slot)
            v_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            return card

        # Add the 4 cards
        cards_layout.addWidget(make_card("Document Request", ["- Barangay Clearance", "- Permits", "- Certificates"], "CHOOSE", lambda: self.stack.setCurrentIndex(3)))
        cards_layout.addWidget(make_card("Health Monitoring", ["- Check Vaccinations", "- Medical Records"], "CHOOSE", lambda: self.stack.setCurrentIndex(4)))
        cards_layout.addWidget(make_card("Complaints & Blotter", ["- File Complaints Online", "- Track Updates"], "CHOOSE", lambda: self.stack.setCurrentIndex(5)))
        cards_layout.addWidget(make_card("SMS Assistance", ["- Receive Barangay Updates", "- Request Notifications"], "CHOOSE", lambda: self.stack.setCurrentIndex(6)))

        main_layout.addLayout(cards_layout)

        # Logout button
        logout = QPushButton("Log out")
        logout.clicked.connect(self.do_logout)
        main_layout.addWidget(logout, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)

    def refresh_user(self):
        u = self.um.current_user
        if u:
            fullname = u.get('fullname') or u.get('username')
            address = u.get('address') or ""
            self.title_lbl.setText(f"WELCOME TO CAPSTEM, {fullname.upper()}")
            self.subtitle_lbl.setText(f"Address: {address}")
        else:
            self.title_lbl.setText("WELCOME TO CAPSTEM")
            self.subtitle_lbl.setText("Fast, reliable and transparent online barangay services")

    def do_logout(self):
        self.um.current_user = None
        QMessageBox.information(self, "Logged out", "You have been logged out.")
        self.stack.setCurrentIndex(0)

class DocumentPage(QWidget):
    def __init__(self, stack: QStackedWidget, um: UserManager, rm: RequestManager):
        super().__init__()
        self.stack = stack
        self.um = um
        self.rm = rm
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("DOCUMENT REQUEST")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.doc_type = QComboBox()
        self.doc_type.addItems([
            "Select Document Type",
            "Barangay Clearance",
            "Certificate of Indigency",
            "Certificate of Residency",
            "Other"
        ])
        self.reason = QPlainTextEdit()
        self.reason.setPlaceholderText("Enter reason...")

        layout.addWidget(QLabel("Document Type:"))
        layout.addWidget(self.doc_type)
        layout.addWidget(QLabel("Reason:"))
        layout.addWidget(self.reason)

        row = QHBoxLayout()
        submit = QPushButton("SUBMIT")
        submit.clicked.connect(self.submit)
        view = QPushButton("View My Requests")
        view.clicked.connect(self.view_my_requests)
        back = QPushButton("Back")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        row.addWidget(submit)
        row.addWidget(view)
        row.addWidget(back)
        layout.addLayout(row)

        # --- TABLE ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Document Type", "Reason", "Status", "Requested On"]
        )

        # Make table fill the space
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table, stretch=1)
        self.setLayout(layout)

    def submit(self):
        try:
            if not self.um.current_user:
                QMessageBox.warning(self, "Login required", "Please login to submit requests.")
                return
            username = self.um.current_user.get("username")
            if not username:
                QMessageBox.critical(self, "Error", "User data missing. Please log out and log in again.")
                return
            dtype = self.doc_type.currentText()
            if dtype == "Select Document Type":
                QMessageBox.warning(self, "Choose", "Select a document type.")
                return
            reason = self.reason.toPlainText().strip()
            if not reason:
                QMessageBox.warning(self, "Fill", "Enter a reason.")
                return
            result = self.rm.submit_document(username, dtype, reason)
            if result:
                QMessageBox.information(self, "Submitted", "Document request submitted (Waiting).")
                self.reason.clear()
                self.view_my_requests()
            else:
                QMessageBox.critical(self, "Error", "Failed to submit document request. Check console for details.")
        except Exception as e:
            QMessageBox.critical(self, "Unexpected Error", f"An unexpected error occurred: {e}")
            print(f"Error in DocumentPage.submit: {e}")

    def view_my_requests(self):
        if not self.um.current_user:
            QMessageBox.warning(self, "Login required", "Please login to view requests.")
            return
        try:
            username = self.um.current_user["username"]
            rows = self.rm.list_documents_for_user(username)
            self.table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(r.get("id", ""))))
                self.table.setItem(i, 1, QTableWidgetItem(r.get("doc_type", "")))
                self.table.setItem(i, 2, QTableWidgetItem(r.get("reason", "")))
                self.table.setItem(i, 3, QTableWidgetItem(r.get("status", "Waiting")))
                self.table.setItem(i, 4, QTableWidgetItem(r.get("requested_on", "")))

            self.table.resizeRowsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load documents: {e}")

class HealthPage(QWidget):
    def __init__(self, stack: QStackedWidget, um: UserManager, rm: RequestManager):
        super().__init__()
        self.stack = stack
        self.um = um
        self.rm = rm
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("HEALTH MONITORING")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.info_label = QLabel("Requests will be made under your logged-in account.")
        layout.addWidget(self.info_label)

        layout.addWidget(QLabel("Select check-up date:"))
        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar)

        row = QHBoxLayout()
        submit = QPushButton("Request Check-up")
        submit.clicked.connect(self.request_checkup)
        view = QPushButton("View My Checkups")
        view.clicked.connect(self.view_my_checkups)
        back = QPushButton("Back")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        row.addWidget(submit)
        row.addWidget(view)
        row.addWidget(back)
        layout.addLayout(row)

        # --- TABLE ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Scheduled Date", "Requested On", "Status", "Notes"]
        )

        # Make table expand fully
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table, stretch=1)
        self.setLayout(layout)

    def request_checkup(self):
        if not self.um.current_user:
            QMessageBox.warning(self, "Login required", "Please login to request a checkup.")
            return
        try:
            username = self.um.current_user.get('username')
            date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
            result = self.rm.submit_checkup(username, date_str)
            if result:
                QMessageBox.information(
                    self, "Requested",
                    f"Checkup requested for {date_str} (Waiting)."
                )
                self.view_my_checkups()
            else:
                QMessageBox.critical(self, "Error", "Failed to submit checkup request.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to request checkup: {e}")

    def view_my_checkups(self):
        if not self.um.current_user:
            QMessageBox.warning(self, "Login required", "Please login to view checkups.")
            return
        try:
            username = self.um.current_user['username']
            rows = self.rm.list_checkups_for_user(username)
            self.table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(r.get("scheduled_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(r.get("requested_on", "")))
                self.table.setItem(i, 2, QTableWidgetItem(r.get("status", "Waiting")))
                self.table.setItem(i, 3, QTableWidgetItem(""))

            self.table.resizeRowsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load checkups: {e}")

class ComplaintPage(QWidget):
    def __init__(self, stack: QStackedWidget, um: UserManager, rm: RequestManager):
        super().__init__()
        self.stack = stack
        self.um = um
        self.rm = rm
        self.photo_path = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("COMPLAINTS & BLOTTER")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.submit_tab(), "Submit Complaint")
        self.tabs.addTab(self.view_tab(), "View My Complaints")
        layout.addWidget(self.tabs, stretch=1)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        layout.addWidget(back_btn)

        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0b3fa3, stop:1 #04255e);
                color: white;
            }
            QLabel {
                color: #e6f0ff;
                font-size: 13px;
            }
            QPlainTextEdit {
                background-color: #dce8ff;
                color: #052043;
                border: 1px solid #a0a0a0;
                border-radius: 6px;
                padding: 6px;
            }
        """)

        self.setLayout(layout)

    def submit_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(15)
        l.setContentsMargins(20, 20, 20, 20)

        l.addWidget(QLabel("Full Name (auto-filled):"))
        self.fullname = QLineEdit()
        self.fullname.setReadOnly(True)
        if self.um.current_user:
            self.fullname.setText(self.um.current_user.get("fullname", self.um.current_user.get("username", "")))
        l.addWidget(self.fullname)

        l.addWidget(QLabel("Complaint Details:"))
        self.complaint_text = QPlainTextEdit()
        self.complaint_text.setPlaceholderText("Enter details of your complaint here...")
        self.complaint_text.setFixedHeight(100)
        l.addWidget(self.complaint_text)

        upload_btn = QPushButton("Upload Photo (Optional)")
        upload_btn.clicked.connect(self.upload_photo)
        l.addWidget(upload_btn)

        submit_btn = QPushButton("Submit Complaint")
        submit_btn.clicked.connect(self.submit_complaint)
        l.addWidget(submit_btn)

        return w

    def view_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(15)
        l.setContentsMargins(20, 20, 20, 20)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Complaint", "Photo", "Submitted On", "Status"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        l.addWidget(self.table, stretch=1)

        refresh_btn = QPushButton("Refresh Complaints")
        refresh_btn.clicked.connect(self.load_my_complaints)
        l.addWidget(refresh_btn)

        return w

    def upload_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Photo", "", "Image Files (*.png *.jpg *.jpeg)")
        if path:
            self.photo_path = path
            QMessageBox.information(self, "Photo Selected", f"Photo selected: {os.path.basename(path)}")

    def submit_complaint(self):
        if not self.um.current_user:
            QMessageBox.warning(self, "Login Required", "Please login to submit a complaint.")
            return
        username = self.um.current_user["username"]
        text = self.complaint_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Missing Info", "Please enter your complaint details.")
            return
        try:
            self.rm.submit_complaint(username, text, self.photo_path)
            QMessageBox.information(self, "Submitted", "Complaint submitted successfully.")
            self.complaint_text.clear()
            self.photo_path = ""
            self.load_my_complaints()
            self.tabs.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to submit complaint:\n{e}")

    def load_my_complaints(self):
        if not self.um.current_user:
            QMessageBox.warning(self, "Login Required", "Please login to view your complaints.")
            return
        username = self.um.current_user["username"]
        try:
            rows = self.rm.list_complaints_for_user(username)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load complaints:\n{e}")
            return
        self.table.setRowCount(0)
        if not rows:
            QMessageBox.information(self, "No Complaints", "You haven't submitted any complaints yet.")
            return
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r.get("id", ""))))
            self.table.setItem(i, 1, QTableWidgetItem(r.get("complaint", "")))
            photo_path = r.get("photo", "")
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if photo_path and os.path.exists(photo_path):
                pixmap = QPixmap(photo_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    img_label.setPixmap(pixmap)
                else:
                    img_label.setText("Invalid Image")
            else:
                img_label.setText("No Photo")
            self.table.setCellWidget(i, 2, img_label)
            self.table.setItem(i, 3, QTableWidgetItem(r.get("submitted_on", "")))
            self.table.setItem(i, 4, QTableWidgetItem(r.get("status", "Waiting")))
        self.table.resizeRowsToContents()

class NotificationPage(QWidget):
    def __init__(self, stack: QStackedWidget, um: UserManager, rm: RequestManager):
        super().__init__()
        self.stack = stack
        self.um = um
        self.rm = rm
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("NOTIFICATIONS")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        info = QLabel("This is a simple offline notification center. Notifications are logged when you submit requests.")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["When", "Type", "Message"])

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(True)

        layout.addWidget(self.table, stretch=1)

        btn_row = QHBoxLayout()
        test_btn = QPushButton("Show My Notifications (Popup)")
        test_btn.clicked.connect(self.show_popup_notifications)
        refresh_btn = QPushButton("Refresh Notifications")
        refresh_btn.clicked.connect(self.load_notifications)
        back = QPushButton("Back")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        btn_row.addWidget(test_btn)
        btn_row.addWidget(refresh_btn)
        btn_row.addWidget(back)

        layout.addLayout(btn_row)
        self.setLayout(layout)

    def load_notifications(self):
        if not self.um.current_user:
            QMessageBox.warning(self, "Login", "Please login to view notifications.")
            return
        try:
            username = self.um.current_user["username"]
            rows = self.rm.list_notifications_for_user(username)
            self.table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(r.get("created_on", "")))
                self.table.setItem(i, 1, QTableWidgetItem(r.get("type", "")))
                msg_item = QTableWidgetItem(r.get("message", ""))
                msg_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                self.table.setItem(i, 2, msg_item)

            self.table.resizeRowsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load notifications: {e}")

    def show_popup_notifications(self):
        if not self.um.current_user:
            QMessageBox.warning(self, "Login required", "Please login first.")
            return
        try:
            username = self.um.current_user["username"]
            rows = self.rm.list_notifications_for_user(username)
            if not rows:
                QMessageBox.information(self, "No notifications", "You have no notifications.")
                return
            latest = rows[-1]
            QMessageBox.information(
                self,
                "New Notification",
                f"{latest.get('type', '')}: {latest.get('message', '')}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show notifications: {e}")

class MainWindow(QStackedWidget):
    def __init__(self):
        super().__init__()
        # Ensure DB exists first
        self.db = Database()

        self.um = UserManager(self.db)
        self.rm = RequestManager(self.db, self.um)

        self.login = LoginScreen(self, self.um, self.rm)
        self.signup = SignupScreen(self, self.um)
        self.dashboard = DashboardScreen(self, self.um, self.rm)
        self.documents = DocumentPage(self, self.um, self.rm)
        self.health = HealthPage(self, self.um, self.rm)
        self.complaints = ComplaintPage(self, self.um, self.rm)
        self.notifs = NotificationPage(self, self.um, self.rm)

        self.addWidget(self.login)
        self.addWidget(self.signup)
        self.addWidget(self.dashboard)
        self.addWidget(self.documents)
        self.addWidget(self.health)
        self.addWidget(self.complaints)
        self.addWidget(self.notifs)

        self.setCurrentIndex(0)
        self.setStyleSheet(APP_STYLE + CARD_STYLE)

    def refresh_all(self):
        try:
            self.dashboard.refresh_user()
        except Exception:
            pass
        try:
            if hasattr(self.complaints, 'fullname') and self.um.current_user:
                self.complaints.fullname.setText(self.um.current_user.get('fullname', self.um.current_user.get('username', '')))
        except Exception:
            pass

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyleSheet(APP_STYLE)

        window = MainWindow()
        window.setWindowTitle("CAPSTEM Barangay Services")
        window.resize(1100, 700)
        window.show()

        print("Application started successfully (using SQLite DB: capstem.db)")

        sys.exit(app.exec())
    except Exception as e:
        print(f"Failed to start application: {e}")
        try:
            QMessageBox.critical(None, "Startup Error", f"Failed to start application: {e}")
        except Exception:
            pass
