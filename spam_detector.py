#username :- admin
#password :- admin123

import customtkinter as ctk
from customtkinter import CTkScrollableFrame, CTkTextbox, CTkFrame, CTkLabel, CTkEntry, CTkButton
from datetime import datetime
import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "spam_detector_db"

class MongoDBManager:
    def __init__(self, uri=MONGO_URI, db_name=DB_NAME):
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.db = self.client[db_name]
            self.keywords_collection = self.db['keywords']
            self.patterns_collection = self.db['patterns']
            self.emails_collection = self.db['emails']
            self.scan_history_collection = self.db['scan_history']
            self.users_collection = self.db['users']
            self.connected = True
            self.initialize_default_data()
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"MongoDB connection failed: {e}")
            self.connected = False
    
    def initialize_default_data(self):
        if self.keywords_collection.count_documents({}) == 0:
            default_keywords = [
                {'keyword': 'urgent', 'weight': 3, 'category': 'pressure'},
                {'keyword': 'winner', 'weight': 5, 'category': 'winner'},
                {'keyword': 'prize', 'weight': 5, 'category': 'winner'},
                {'keyword': 'lottery', 'weight': 5, 'category': 'financial'},
                {'keyword': 'million', 'weight': 4, 'category': 'financial'},
                {'keyword': 'inheritance', 'weight': 5, 'category': 'financial'},
                {'keyword': 'claim', 'weight': 3, 'category': 'action'},
                {'keyword': 'verify', 'weight': 3, 'category': 'security'},
                {'keyword': 'suspended', 'weight': 4, 'category': 'security'},
                {'keyword': 'viagra', 'weight': 5, 'category': 'pharmacy'},
                {'keyword': 'act now', 'weight': 4, 'category': 'pressure'},
                {'keyword': 'click here', 'weight': 3, 'category': 'action'},
            ]
            self.keywords_collection.insert_many(default_keywords)
        
        if self.patterns_collection.count_documents({}) == 0:
            default_patterns = [
                {'pattern': r'\b[A-Z]{5,}\b', 'weight': 3, 'description': 'Excessive capitals'},
                {'pattern': r'!{2,}', 'weight': 2, 'description': 'Multiple exclamation marks'},
                {'pattern': r'\${1,}\d+(?:,\d{3})*(?:\.\d{2})?', 'weight': 3, 'description': 'Large money amounts'},
                {'pattern': r'(?:click|tap)\s+(?:here|now|below)', 'weight': 4, 'description': 'Suspicious links'},
                {'pattern': r'\b(?:100%|guaranteed)\b', 'weight': 3, 'description': 'Unrealistic promises'},
            ]
            self.patterns_collection.insert_many(default_patterns)
        
        # Add default user if none exists
        if self.users_collection.count_documents({}) == 0:
            default_user = {'username': 'admin', 'password': 'admin123'}
            self.users_collection.insert_one(default_user)
    
    def verify_user(self, username, password):
        if not self.connected:
            return False
        user = self.users_collection.find_one({'username': username, 'password': password})
        return user is not None
    
    def get_all_keywords(self):
        if not self.connected:
            return {}
        return {doc['keyword']: doc['weight'] for doc in self.keywords_collection.find()}
    
    def get_all_patterns(self):
        if not self.connected:
            return []
        return [(doc['pattern'], doc['weight'], doc['description']) for doc in self.patterns_collection.find()]
    
    def add_keyword(self, keyword, weight, category='custom'):
        if not self.connected:
            return False
        self.keywords_collection.insert_one({'keyword': keyword.lower(), 'weight': weight, 'category': category, 'created_at': datetime.now()})
        return True
    
    def delete_keyword(self, keyword):
        if not self.connected:
            return False
        self.keywords_collection.delete_one({'keyword': keyword.lower()})
        return True
    
    def add_pattern(self, pattern, weight, description):
        if not self.connected:
            return False
        self.patterns_collection.insert_one({'pattern': pattern, 'weight': weight, 'description': description, 'created_at': datetime.now()})
        return True
    
    def delete_pattern(self, pattern):
        if not self.connected:
            return False
        self.patterns_collection.delete_one({'pattern': pattern})
        return True
    
    def save_email(self, email):
        if not self.connected:
            return None
        result = self.emails_collection.insert_one({**email, 'created_at': datetime.now()})
        return result.inserted_id
    
    def get_all_emails(self):
        if not self.connected:
            return []
        return list(self.emails_collection.find())

class SpamDetector:
    def __init__(self, mongo_manager):
        self.mongo_manager = mongo_manager
        self.refresh_data()
        self.spam_threshold = 15
    
    def refresh_data(self):
        self.keyword_weights = self.mongo_manager.get_all_keywords()
        self.suspicious_patterns = self.mongo_manager.get_all_patterns()
       
    def analyze_keywords(self, text):
        text_lower = text.lower()
        score = 0
        found_keywords = {}
        for keyword, weight in self.keyword_weights.items():
            count = text_lower.count(keyword)
            if count > 0:
                score += weight * min(count, 3)
                found_keywords[keyword] = count
        return score, found_keywords
   
    def analyze_patterns(self, text):
        score = 0
        detected = []
        for pattern, weight, description in self.suspicious_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                count = len(matches)
                score += weight * min(count, 3)
                detected.append(f"{description} ({count}x)")
        return score, detected

    def analyze_structure(self, email):
        score = 0
        issues = []
        subject = email.get('subject', '')
        if not subject:
            score += 5
            issues.append("Missing subject")
        elif subject.isupper():
            score += 3
            issues.append("Subject in all caps")
        
        sender = email.get('sender', '')
        if not sender or '@' not in sender:
            score += 5
            issues.append("Invalid sender")
        return score, issues
   
    def detect(self, email):
        full_text = f"{email.get('subject', '')} {email.get('body', '')}"
        keyword_score, found_keywords = self.analyze_keywords(full_text)
        pattern_score, found_patterns = self.analyze_patterns(full_text)
        structure_score, structure_issues = self.analyze_structure(email)
        total_score = keyword_score + pattern_score + structure_score
        
        classification = "SPAM" if total_score >= self.spam_threshold else "LEGITIMATE"
        confidence = min(100, int((total_score / self.spam_threshold) * 50 + 50)) if classification == "SPAM" else min(100, int(100 - (total_score / self.spam_threshold) * 50))
        
        return {
            'classification': classification,
            'confidence': confidence,
            'total_score': total_score,
            'keyword_score': keyword_score,
            'pattern_score': pattern_score,
            'structure_score': structure_score,
            'found_keywords': found_keywords,
            'found_patterns': found_patterns,
            'structure_issues': structure_issues,
            'threshold': self.spam_threshold,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'email_id': email.get('id', 'N/A')
        }

class ReportGenerator:
    @staticmethod
    def generate_report(result, email):
        badge = "🚨 SPAM" if result['classification'] == "SPAM" else "✅ LEGITIMATE"
        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║                  SPAM DETECTION REPORT                            ║
╚═══════════════════════════════════════════════════════════════╝

📧 Email ID: {result['email_id']}
✉️  From: {email.get('sender', 'N/A')}
📌 Subject: {email.get('subject', 'N/A')}
🕒 Scanned: {result['timestamp']}

🔍 RESULT: {badge}   Confidence: {result['confidence']}% 

📊 Total Spam Score: {result['total_score']} / {result['threshold']}

📈 Score Breakdown:
   • Keywords: {result['keyword_score']}
   • Patterns: {result['pattern_score']}
   • Structure: {result['structure_score']}

⚠️  Suspicious Keywords ({len(result['found_keywords'])}):
"""
        if result['found_keywords']:
            for kw, count in result['found_keywords'].items():
                report += f"   • '{kw}' ({count}x)\n"
        else:
            report += "   None detected\n"

        report += f"\n🔎 Suspicious Patterns ({len(result['found_patterns'])}):\n"
        report += "\n".join(f"   • {p}" for p in result['found_patterns']) if result['found_patterns'] else "   None detected\n"

        report += f"\n🗝️  Structure Issues ({len(result['structure_issues'])}):\n"
        report += "\n".join(f"   • {i}" for i in result['structure_issues']) if result['structure_issues'] else "   None detected\n"

        report += "\n" + "═" * 67 + "\n"
        report += "⚠️  RECOMMENDATION: Move to spam or delete this email.\n" if result['classification'] == "SPAM" else "✅ RECOMMENDATION: This email appears safe.\n"
        report += "═" * 67
        return report

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Spam Detector - Login")
        self.geometry("420x350")
        self.resizable(False, False)
        
        self.mongo_manager = MongoDBManager()
        self.logged_in = False
        
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (420 // 2)
        y = (self.winfo_screenheight() // 2) - (350 // 2)
        self.geometry(f"420x350+{x}+{y}")
        
        self.create_login_ui()
    
    def create_login_ui(self):
        main_frame = CTkFrame(self, fg_color="#1e1e1e", corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        CTkLabel(main_frame, text="🔐 Spam Detector", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 10))
        CTkLabel(main_frame, text="Login to continue", font=ctk.CTkFont(size=12), text_color="#888888").pack(pady=(0, 30))
        
        # Username field
        username_frame = CTkFrame(main_frame, fg_color="transparent")
        username_frame.pack(pady=10, padx=40, fill="x")
        CTkLabel(username_frame, text="Username:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.username_entry = CTkEntry(username_frame, width=320, placeholder_text="Enter username", height=35)
        self.username_entry.pack(pady=5)
        
        # Password field
        password_frame = CTkFrame(main_frame, fg_color="transparent")
        password_frame.pack(pady=10, padx=40, fill="x")
        CTkLabel(password_frame, text="Password:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.password_entry = CTkEntry(password_frame, width=320, placeholder_text="Enter password", show="●", height=35)
        self.password_entry.pack(pady=5)
        
        # Error label
        self.error_label = CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11), text_color="#ff4444", wraplength=320)
        self.error_label.pack(pady=5)
        
        # Login button
        CTkButton(main_frame, text="Login", command=self.attempt_login, width=320, height=40, 
                  font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15, padx=40)
        
        # Default credentials info
        CTkLabel(main_frame, text="Default: admin / admin123", font=ctk.CTkFont(size=10), text_color="#666666").pack(pady=(5, 0))
        
        # Bind Enter key to login for both fields
        self.username_entry.bind("<Return>", lambda e: self.attempt_login())
        self.password_entry.bind("<Return>", lambda e: self.attempt_login())
    
    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.error_label.configure(text="⚠️ Please enter both username and password")
            return
        
        if self.mongo_manager.verify_user(username, password):
            self.logged_in = True
            self.destroy()
        else:
            self.error_label.configure(text="❌ Invalid username or password")
            self.password_entry.delete(0, 'end')
            self.username_entry.focus()

class ModernSpamDetectorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Email Spam Detector with MongoDB")
        self.geometry("1200x800")
        self.minsize(1000, 650)
        
        self.mongo_manager = MongoDBManager()
        if not self.mongo_manager.connected:
            self.show_connection_error()
        
        self.detector = SpamDetector(self.mongo_manager)
        self.emails = []
        self.next_id = 1
        self.email_frames = {}
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()
        self.load_emails_from_db()
    
    def show_connection_error(self):
        error_window = ctk.CTkToplevel(self)
        error_window.title("MongoDB Connection Error")
        error_window.geometry("500x200")
        ctk.CTkLabel(error_window, text="⚠️ MongoDB Connection Failed", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ff4444").pack(pady=20)
        ctk.CTkLabel(error_window, text="Please ensure MongoDB is running\nand connection URI is correct").pack(pady=10)
        ctk.CTkButton(error_window, text="OK", command=error_window.destroy).pack(pady=10)
    
    def create_widgets(self):
        main_container = CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=3)
        main_container.grid_columnconfigure(1, weight=2)
        
        # Left Panel
        left_panel = CTkFrame(main_container, fg_color="#1e1e1e", corner_radius=10)
        left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 5))
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
        CTkLabel(left_panel, text="📧 Email Composer", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=10, padx=10, sticky="w")
        
        form_frame = CTkFrame(left_panel, fg_color="transparent")
        form_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        form_frame.grid_columnconfigure(1, weight=1)
        
        CTkLabel(form_frame, text="From:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", pady=5)
        self.sender_entry = CTkEntry(form_frame, placeholder_text="sender@example.com")
        self.sender_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        
        CTkLabel(form_frame, text="Subject:", font=ctk.CTkFont(size=12)).grid(row=1, column=0, sticky="w", pady=5)
        self.subject_entry = CTkEntry(form_frame, placeholder_text="Email subject")
        self.subject_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        
        CTkLabel(form_frame, text="Body:", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="nw", pady=5)
        self.body_text = CTkTextbox(form_frame, height=150)
        self.body_text.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        
        btn_frame = CTkFrame(left_panel, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=10, padx=10)
        CTkButton(btn_frame, text="➕ Add Email", command=self.add_email, width=120).pack(side="left", padx=5)
        CTkButton(btn_frame, text="🗑️ Clear All", command=self.clear_all_emails, width=120, fg_color="#ff4444", hover_color="#cc0000").pack(side="left", padx=5)
        CTkButton(btn_frame, text="⚙️ Manage DB", command=self.open_db_manager, width=120).pack(side="left", padx=5)
        
        # Right Panel
        right_panel = CTkFrame(main_container, fg_color="#1e1e1e", corner_radius=10)
        right_panel.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(5, 0))
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        CTkLabel(right_panel, text="📬 Email Queue", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=10, padx=10, sticky="w")
        
        self.email_list_frame = CTkScrollableFrame(right_panel, fg_color="#2b2b2b")
        self.email_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.email_list_frame.grid_columnconfigure(0, weight=1)
    
    def add_email(self):
        sender = self.sender_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_text.get("1.0", "end-1c").strip()
        
        if not sender or not subject or not body:
            self.show_message("Error", "Please fill all fields")
            return
        
        email = {'id': self.next_id, 'sender': sender, 'subject': subject, 'body': body}
        self.emails.append(email)
        self.mongo_manager.save_email(email)
        self.create_email_card(email)
        self.next_id += 1
        self.clear_form()
    
    def clear_form(self):
        self.sender_entry.delete(0, 'end')
        self.subject_entry.delete(0, 'end')
        self.body_text.delete("1.0", 'end')
    
    def create_email_card(self, email):
        card = CTkFrame(self.email_list_frame, fg_color="#3a3a3a", corner_radius=8)
        card.grid(sticky="ew", pady=5, padx=5)
        card.grid_columnconfigure(0, weight=1)
        
        CTkLabel(card, text=f"✉️ {email['subject'][:30]}...", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
        CTkLabel(card, text=f"From: {email['sender']}", font=ctk.CTkFont(size=10), anchor="w", text_color="#888888").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        
        CTkButton(card, text="🔍 Scan", command=lambda e=email: self.scan_email(e), width=80, height=25).grid(row=0, column=1, rowspan=2, padx=10, pady=5)
        
        self.email_frames[email['id']] = card
    
    def scan_email(self, email):
        self.detector.refresh_data()
        result = self.detector.detect(email)
        report = ReportGenerator.generate_report(result, email)
        
        result_window = ctk.CTkToplevel(self)
        result_window.title(f"Scan Result - {email['subject'][:30]}")
        result_window.geometry("800x600")
        
        report_text = CTkTextbox(result_window, font=ctk.CTkFont(family="Courier", size=11))
        report_text.pack(fill="both", expand=True, padx=10, pady=10)
        report_text.insert("1.0", report)
        report_text.configure(state="disabled")
    
    def clear_all_emails(self):
        self.emails.clear()
        for widget in self.email_list_frame.winfo_children():
            widget.destroy()
        self.email_frames.clear()
    
    def load_emails_from_db(self):
        db_emails = self.mongo_manager.get_all_emails()
        for email in db_emails:
            email['id'] = self.next_id
            self.emails.append(email)
            self.create_email_card(email)
            self.next_id += 1
    
    def show_message(self, title, message):
        msg = ctk.CTkToplevel(self)
        msg.title(title)
        msg.geometry("300x150")
        CTkLabel(msg, text=message, font=ctk.CTkFont(size=14)).pack(pady=30)
        CTkButton(msg, text="OK", command=msg.destroy).pack(pady=10)
    
    def open_db_manager(self):
        db_window = ctk.CTkToplevel(self)
        db_window.title("Database Manager")
        db_window.geometry("900x600")
        
        tabview = ctk.CTkTabview(db_window)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Keywords Tab
        kw_tab = tabview.add("Keywords")
        CTkLabel(kw_tab, text="Add New Keyword", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        add_frame = CTkFrame(kw_tab)
        add_frame.pack(pady=10, padx=10, fill="x")
        CTkLabel(add_frame, text="Keyword:").grid(row=0, column=0, padx=5, pady=5)
        kw_entry = CTkEntry(add_frame, width=200)
        kw_entry.grid(row=0, column=1, padx=5, pady=5)
        CTkLabel(add_frame, text="Weight:").grid(row=0, column=2, padx=5, pady=5)
        weight_entry = CTkEntry(add_frame, width=80)
        weight_entry.grid(row=0, column=3, padx=5, pady=5)
        
        def add_kw():
            kw = kw_entry.get().strip()
            try:
                weight = int(weight_entry.get().strip())
                if kw and self.mongo_manager.add_keyword(kw, weight):
                    self.show_message("Success", "Keyword added!")
                    kw_entry.delete(0, 'end')
                    weight_entry.delete(0, 'end')
            except ValueError:
                self.show_message("Error", "Weight must be a number")
        
        CTkButton(add_frame, text="Add", command=add_kw).grid(row=0, column=4, padx=5, pady=5)
        
        # Patterns Tab
        pt_tab = tabview.add("Patterns")
        CTkLabel(pt_tab, text="Add New Pattern", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        pt_frame = CTkFrame(pt_tab)
        pt_frame.pack(pady=10, padx=10, fill="x")
        CTkLabel(pt_frame, text="Pattern:").grid(row=0, column=0, padx=5, pady=5)
        pt_entry = CTkEntry(pt_frame, width=300)
        pt_entry.grid(row=0, column=1, padx=5, pady=5)
        CTkLabel(pt_frame, text="Weight:").grid(row=1, column=0, padx=5, pady=5)
        pt_weight = CTkEntry(pt_frame, width=80)
        pt_weight.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        CTkLabel(pt_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5)
        pt_desc = CTkEntry(pt_frame, width=300)
        pt_desc.grid(row=2, column=1, padx=5, pady=5)
        
        def add_pt():
            pattern = pt_entry.get().strip()
            desc = pt_desc.get().strip()
            try:
                weight = int(pt_weight.get().strip())
                if pattern and desc and self.mongo_manager.add_pattern(pattern, weight, desc):
                    self.show_message("Success", "Pattern added!")
                    pt_entry.delete(0, 'end')
                    pt_weight.delete(0, 'end')
                    pt_desc.delete(0, 'end')
            except ValueError:
                self.show_message("Error", "Weight must be a number")
        
        CTkButton(pt_frame, text="Add Pattern", command=add_pt).grid(row=3, column=1, padx=5, pady=10, sticky="w")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Show login window first
    login_window = LoginWindow()
    login_window.mainloop()
    
    # If login successful, show main app
    if login_window.logged_in:
        app = ModernSpamDetectorApp()
        app.mainloop()