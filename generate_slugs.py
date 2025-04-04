from app import create_app, db
from app.models import Article
import re
import unicodedata

# دالة توليد slug
def generate_slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)

app = create_app()

with app.app_context():
    articles = Article.query.all()
    count = 0

    for article in articles:
        if not article.slug:
            slug = generate_slug(article.title)
            # تأكد من تفرده
            original_slug = slug
            i = 1
            while Article.query.filter_by(slug=slug).first():
                slug = f"{original_slug}-{i}"
                i += 1

            article.slug = slug
            count += 1

    db.session.commit()
    print(f"✅ تم إصلاح {count} مقال بدون slug.")
