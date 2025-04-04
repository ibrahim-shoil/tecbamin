# tecBamin 🧠✨

**tecBamin** is a modern Arabic blog built with **Flask** that focuses on publishing high-quality, categorized articles in technology, science, reviews, and more — all through a clean, responsive, and fast-loading design.

---

## 🚀 Features

- 📰 Article publishing system with categories and tags  
- 🖼️ Image upload with automatic resizing  
- 🧭 Table of Contents generation  
- 💬 AJAX-based comment system with reply support  
- 📊 View counter and analytics-ready  
- 🔍 Advanced search with category filtering and smart sorting  
- 🌙 Clean, responsive design tailored for RTL content  
- 🔐 Admin-only access panel with secret URL paths  
- 📤 Social media sharing buttons  
- 📥 Lazy image loading for better performance  
- 🧠 SEO-friendly metadata and OG tags  
- 🛠️ External Ads loader from JSON file (configurable)

---

## 🧑‍💻 Tech Stack

- **Backend**: Python (Flask)  
- **Frontend**: HTML5, CSS3, Bootstrap 5  
- **Database**: SQLite (for development)  
- **Authentication**: Session-based admin panel  
- **Templating**: Jinja2  
- **ORM**: SQLAlchemy with Alembic for migrations  

---

## 🔧 Getting Started

To run **tecBamin** locally:

```bash
git clone https://github.com/ibrahim-shoil/tecbamin.git
cd tecbamin
python -m venv venv
venv\Scripts\activate     # On Windows
pip install -r requirements.txt
python run.py
