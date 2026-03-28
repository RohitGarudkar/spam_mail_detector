# 📧 Spam Mail Detection System

A Python-based **Spam Mail Detection System** developed using **Tkinter (CustomTkinter)** for the graphical user interface and **MongoDB** for database management.

This project uses a **keyword-based and pattern-based spam detection approach** to analyze email content and classify messages as **SPAM** or **LEGITIMATE**.

---

## 🚀 Features

- 🔐 User Login Authentication
- 📧 Email Composer Interface
- 🧠 Keyword-based Spam Detection
- 🔍 Regex Pattern-based Detection
- 📊 Spam Score Calculation
- 📈 Confidence Percentage
- 🗄️ MongoDB Integration
- 📝 Scan Report Generation
- ⚙️ Database Manager for Keywords and Patterns
- 🌙 Modern Dark UI using CustomTkinter

---

## 🛠️ Technologies Used

- **Python**
- **Tkinter / CustomTkinter**
- **MongoDB**
- **Regex (re module)**
- **PyMongo**

---

## 🧠 Working Principle

The system detects spam emails using:

### 1. Keyword-Based Analysis
It checks for suspicious words such as:

- urgent
- winner
- lottery
- claim
- verify
- suspended
- click here
- act now

Each keyword has a predefined **spam weight**.

---

### 2. Pattern-Based Analysis
The system uses regular expressions to detect suspicious patterns such as:

- Multiple exclamation marks (`!!`)
- Excessive capital letters
- Large money amounts
- Suspicious links
- Unrealistic promises

---

### 3. Structure Analysis
The system also checks:

- Missing subject
- Invalid sender email
- Subject written in all caps

---

## 📊 Spam Classification

The email is classified based on the total spam score.

- **SPAM** → Score ≥ Threshold
- **LEGITIMATE** → Score < Threshold

Default threshold value:

```python
15
```

---

## 🗄️ Database Collections

MongoDB stores:

- `users`
- `keywords`
- `patterns`
- `emails`
- `scan_history`

---

## 🔐 Default Login Credentials

```text
Username: admin
Password: admin123
```

---

## ▶️ How to Run the Project

### Step 1: Install Required Libraries

```bash
pip install customtkinter pymongo
```

---

### Step 2: Start MongoDB

Make sure MongoDB server is running locally:

```text
mongodb://localhost:27017/
```

---

### Step 3: Run the Project

```bash
python spam_detector.py
```

---

## 📌 Project Objective

The main objective of this project is to provide a simple spam detection mechanism using **rule-based filtering techniques** for educational and mini-project purposes.

---

## 📷 Output

The system provides:

- Spam classification result
- Score breakdown
- Detected suspicious keywords
- Detected suspicious patterns
- Final recommendation

---

## 👨‍💻 Developed By

**Rohit Garudkar**  
MCA Mini Project
