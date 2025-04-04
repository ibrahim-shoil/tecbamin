import os
import re
import unicodedata
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    abort,
    request,
    session,
    url_for,
    jsonify,
    request,
    Response,
    send_from_directory,
)
from werkzeug.utils import secure_filename

from . import db
from .forms import ArticleForm, LoginForm, CommentForm
from .models import Article, Comment, Tag

from slugify import slugify as slugify_lib
from app.utils import generate_slug
from time import time
from app.models import Tag
from sqlalchemy.sql.expression import func  # لازم تكون مستورد func


from .forms import ContactForm
from .utils import send_email_smtp

from app.models import Author

# ✅ مضافة لحساب عدد التعليقات لكل مقال
from sqlalchemy import func

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString


main = Blueprint("main", __name__)


# ----------------------------
# ✏️ الصفحات غير المنشورة
# ----------------------------
@main.route("/hidden-unpublished-articles")
def unpublished_articles():
    if not session.get("admin"):
        abort(404)

    articles = (
        Article.query.filter_by(is_published=False)
        .order_by(Article.date_posted.desc())
        .all()
    )
    return render_template("unpublished.html", articles=articles)


@main.app_errorhandler(403)
def forbidden_error(error):
    return render_template("403.html"), 403


@main.app_errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@main.app_errorhandler(405)
def method_not_allowed(error):
    return render_template("405.html"), 405


@main.app_errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500


@main.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy.html")


@main.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        subject = "📨 رسالة جديدة من نموذج التواصل"
        body = f"""
        <h3>اسم المُرسل:</h3> <p>{form.name.data}</p>
        <h3>البريد الإلكتروني:</h3> <p>{form.email.data}</p>
        <h3>محتوى الرسالة:</h3> <p>{form.message.data.replace('\n', '<br>')}</p>
        """
        try:
            send_email_smtp(subject, body, form.email.data, form.name.data)
            flash("✅ تم إرسال رسالتك بنجاح!", "success")
        except Exception as e:
            flash("❌ حدث خطأ أثناء إرسال الرسالة. يرجى المحاولة لاحقًا.", "danger")

        return redirect(url_for("main.contact"))

    return render_template("contact.html", form=form)


@main.route("/about")
def about():
    return render_template("about.html")


# ----------------------------
# 📌 الصفحة الرئيسية
# ----------------------------
@main.route("/")
@main.route("/page/<int:page>")
def home(page=1):
    per_page = 6
    pagination = (
        Article.query.filter_by(is_published=True)
        .order_by(Article.date_posted.desc())
        .paginate(page=page, per_page=per_page)
    )
    articles = pagination.items

    # ✅ نحضر عدد التعليقات لكل مقال
    articles_with_comments = []
    for article in articles:
        comment_count = Comment.query.filter_by(
            article_id=article.id, is_approved=True
        ).count()
        articles_with_comments.append(
            {"article": article, "comment_count": comment_count}
        )

    return render_template(
        "home.html",
        articles_with_comments=articles_with_comments,
        pagination=pagination,
    )


# ----------------------------
# 👁 عرض مقال + التعليقات
# ----------------------------
# ----------------------------
# ✅ عرض مقال + التعليقات + النموذج
# ----------------------------
@main.route("/article/<string:slug>", methods=["GET", "POST"])
def article_detail(slug):
    article = Article.query.filter_by(
        slug=slug, is_published=True).first_or_404()
    article.views += 1
    db.session.commit()

    form = CommentForm()
    is_admin = session.get("admin")

    # ✅ التعامل مع التعليقات
    if (
        is_admin and request.method == "POST" and form.content.data
    ) or form.validate_on_submit():
        comment = Comment(
            name="إدارة الموقع" if is_admin else form.name.data,
            content=form.content.data,
            article_id=article.id,
            is_approved=True if is_admin else False,
        )
        db.session.add(comment)
        db.session.commit()

        flash(
            (
                "✅ تم نشر تعليقك مباشرة"
                if is_admin
                else "✅ تم إرسال تعليقك وهو الآن قيد المراجعة"
            ),
            "success",
        )
        return redirect(url_for("main.article_detail", slug=slug))

    # ✅ جلب التعليقات
    if is_admin:
        all_comments = (
            Comment.query.filter_by(article_id=article.id, parent_id=None)
            .order_by(Comment.date.desc())
            .all()
        )
        total_comments = len(all_comments)
        comments = all_comments[:6]
    else:
        comments = (
            Comment.query.filter_by(
                article_id=article.id, is_approved=True, parent_id=None
            )
            .order_by(Comment.date.desc())
            .limit(6)
            .all()
        )
        total_comments = Comment.query.filter_by(
            article_id=article.id, is_approved=True, parent_id=None
        ).count()

    # ✅ المقالات المرتبطة يدويًا
    manual_related = article.related

    # ✅ المقالات المقترحة عشوائيًا من نفس التصنيف
    suggested_articles = (
        Article.query.filter(
            Article.id != article.id,
            Article.category == article.category,
            Article.is_published == True,
            ~Article.id.in_([a.id for a in manual_related]),
        )
        .order_by(func.random())
        .limit(4)
        .all()
    )

    # ✅ إعلان وهمي داخل المقال
    ad_block = """
        <div class="in-article-ad text-center my-4">
            <img src="https://i.ibb.co/9WDNYJp/ads-placeholder.png" 
                alt="إعلان وهمي" 
                class="img-fluid rounded shadow-sm"
                style="max-height: 200px; width: 100%; object-fit: cover;">
        </div>
    """

    return render_template(
        "article.html",
        article=article,
        manual_related=manual_related,
        suggested_articles=suggested_articles,
        form=form,
        comments=comments,
        total_comments=total_comments,
        is_admin=is_admin,
        ad_block=ad_block,
    )


# ----------------------------
# 🗂️ تعليقات المقال للأدمن
# ----------------------------
@main.route("/article-comments-secure/<int:article_id>")
def article_comments(article_id):
    if not session.get("admin"):
        abort(404)
    article = Article.query.get_or_404(article_id)
    comments = (
        Comment.query.filter_by(article_id=article.id)
        .order_by(Comment.date.desc())
        .all()
    )
    return render_template("article_comments.html", article=article, comments=comments)


@main.route("/delete-comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    if not session.get("admin"):
        return redirect(url_for("main.login"))
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("تم حذف التعليق بنجاح ✅", "success")
    return redirect(request.referrer or url_for("main.dashboard"))


# ----------------------------
# ✏️ حذف كل المقالات
# ----------------------------
@main.route("/delete_all_articles_secure", methods=["POST"])
def delete_all_articles():
    if "admin" not in session:
        abort(404)

    try:
        num_deleted = Article.query.delete()
        db.session.commit()
        flash(f"تم حذف {num_deleted} مقال من قاعدة البيانات.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"حدث خطأ أثناء الحذف: {str(e)}", "danger")

    return redirect(url_for("main.dashboard"))


# ----------------------------
# ✏️ حذف كل التعليقات
# ----------------------------
@main.route("/delete_all_comments_secure", methods=["POST"])
def delete_all_comments():
    if "admin" not in session:
        abort(404)

    try:
        num_deleted = Comment.query.delete()
        db.session.commit()
        flash(f"✅ تم حذف {num_deleted} تعليق من قاعدة البيانات.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ حدث خطأ أثناء حذف التعليقات: {str(e)}", "danger")

    return redirect(url_for("main.dashboard"))


@main.route("/approve-comment/<int:comment_id>", methods=["POST"])
def approve_comment(comment_id):
    if not session.get("admin"):
        abort(404)

    comment = Comment.query.get_or_404(comment_id)
    comment.is_approved = True
    db.session.commit()
    flash("تمت الموافقة على التعليق ✅", "success")
    return redirect(request.referrer or url_for("main.dashboard"))


@main.route("/get_comments/<string:slug>")
def get_comments(slug):
    count = int(request.args.get("count", 6))
    article = Article.query.filter_by(
        slug=slug, is_published=True).first_or_404()
    is_admin = session.get("admin")

    if is_admin:
        base_query = Comment.query.filter_by(
            article_id=article.id, parent_id=None)
    else:
        base_query = Comment.query.filter_by(
            article_id=article.id, is_approved=True, parent_id=None
        )

    total_comments = base_query.count()
    comments = base_query.order_by(Comment.date.desc()).limit(count).all()

    comment_data = []
    for comment in comments:
        replies_query = Comment.query.filter_by(parent_id=comment.id)
        if not is_admin:
            replies_query = replies_query.filter_by(is_approved=True)

        replies = replies_query.order_by(Comment.date.asc()).all()

        replies_data = [
            {
                "id": reply.id,  # ✅ مهم علشان الرد يظهر
                "name": reply.name,
                "content": reply.content,
                "date": reply.date.strftime("%Y-%m-%d %H:%M"),
            }
            for reply in replies
        ]

        comment_data.append(
            {
                "id": comment.id,
                "name": comment.name,
                "content": comment.content,
                "date": comment.date.strftime("%Y-%m-%d %H:%M"),
                "replies": replies_data,
            }
        )

    return jsonify({"comments": comment_data, "has_more": count < total_comments})


# ----------------------------
# ✅ الرد على تعليق معين (للأدمن فقط)
# ----------------------------
@main.route("/reply-comment/<int:comment_id>", methods=["POST"])
def reply_comment(comment_id):
    if not session.get("admin"):
        abort(404)

    parent_comment = Comment.query.get_or_404(comment_id)

    content = request.form.get("content", "").strip()

    if content:
        reply = Comment(
            name="إدارة الموقع",
            content=content,
            article_id=parent_comment.article_id,
            parent_id=parent_comment.id,
            is_approved=True,
        )
        db.session.add(reply)
        db.session.commit()
        flash("✅ تم إضافة الرد بنجاح", "success")
    else:
        flash("❌ لا يمكن إرسال رد فارغ", "danger")

    return redirect(url_for("main.article_detail", slug=parent_comment.article.slug))


# ----------------------------
# 🔐 تسجيل الدخول / الخروج
# ----------------------------
# 🔐 تسجيل الدخول بالرابط السري فقط
@main.route("/racJu4-tazpyp-mefqyx", methods=["GET", "POST"])
def login():
    if "admin" in session:
        flash("أنت مسجل دخول بالفعل")
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        if (
            form.username.data == "admin"
            and form.password.data == "racJu4-tazpyp-mefqyx"
        ):
            session["admin"] = True
            flash("تم تسجيل الدخول بنجاح", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("بيانات الدخول غير صحيحة")
    return render_template("login.html", form=form)


@main.route("/logout")
def logout():
    session.pop("admin", None)
    flash("تم تسجيل الخروج بنجاح", "success")
    return redirect(url_for("main.login"))


# ----------------------------
# 🛠 لوحة التحكم
# ----------------------------
@main.route("/admin-panel-38tmujf")
def dashboard():
    if "admin" not in session:
        abort(404)

    # ترقيم المقالات
    page = request.args.get("page", 1, type=int)
    per_page = 10

    search_query = request.args.get("q", "")
    if search_query:
        articles_query = Article.query.filter(
            Article.title.contains(search_query)
            | Article.content.contains(search_query)
        )
    else:
        articles_query = Article.query

    articles_query = articles_query.order_by(Article.date_posted.desc())
    pagination = articles_query.paginate(
        page=page, per_page=per_page, error_out=False)
    articles = pagination.items

    # ✅ ترقيم التعليقات بشكل منفصل
    comments_page = request.args.get("comments_page", 1, type=int)
    comments_pagination = Comment.query.order_by(Comment.date.desc()).paginate(
        page=comments_page, per_page=10, error_out=False
    )
    comments = comments_pagination.items

    return render_template(
        "dashboard.html",
        articles=articles,
        pagination=pagination,
        comments=comments,
        comments_pagination=comments_pagination,
    )


@main.route("/dashboard/load_more_articles")
def load_more_articles():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "")

    query = Article.query
    if q:
        query = query.filter(Article.title.ilike(f"%{q}%"))

    pagination = query.order_by(Article.date_posted.desc()).paginate(
        page=page, per_page=10
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_template(
            "partials/_article_rows.html", articles=pagination.items)
        return jsonify({"html": html, "has_next": pagination.has_next})

    return redirect(url_for("main.dashboard"))


@main.route("/dashboard/load_more_comments")
def load_more_comments():
    page = request.args.get("comments_page", 1, type=int)
    q = request.args.get("q", "")

    query = Comment.query
    if q:
        query = query.join(Article).filter(Article.title.ilike(f"%{q}%"))

    pagination = query.order_by(
        Comment.date.desc()).paginate(page=page, per_page=10)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_template(
            "partials/_comment_rows.html", comments=pagination.items)
        return jsonify({"html": html, "has_next": pagination.has_next})

    return redirect(url_for("main.dashboard"))


# ----------------------------
# ➕ إضافة مقال (مع رفع صورة)
# ----------------------------
@main.route("/new-article-93kfjq", methods=["GET", "POST"])
def new_article():
    if "admin" not in session:
        abort(404)

    form = ArticleForm()
    form.author.choices = [(a.id, a.name) for a in Author.query.all()]
    form.related_articles.choices = [(a.id, a.title)
                                     for a in Article.query.all()]

    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            image = form.image.data
            image_filename = secure_filename(image.filename)
            upload_folder = os.path.abspath(
                os.path.join(current_app.root_path, "..", "static", "uploads")
            )
            os.makedirs(upload_folder, exist_ok=True)
            saved_path = os.path.join(upload_folder, image_filename)
            image.save(saved_path)
            image_path = image_filename
        elif form.image_url.data:
            image_path = form.image_url.data

        slug = generate_slug(form.title.data)
        existing_slug = Article.query.filter_by(slug=slug).first()
        counter = 1
        original_slug = slug
        while existing_slug:
            slug = f"{original_slug}-{counter}"
            existing_slug = Article.query.filter_by(slug=slug).first()
            counter += 1

        article = Article(
            title=form.title.data,
            author_id=form.author.data,
            content=form.content.data,
            slug=slug,
            category=form.category.data,
            is_published=form.is_published.data,
            image_path=image_path,
        )

        # ✅ ربط المقالات المرتبطة
        article.related = Article.query.filter(
            Article.id.in_(form.related_articles.data)
        ).all()

        # ✅ معالجة التاجز
        tag_names = [t.strip() for t in form.tags.data.split(",") if t.strip()]
        tags = []
        for name in tag_names:
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name)
                db.session.add(tag)
            tags.append(tag)
        article.tags = tags

        db.session.add(article)
        db.session.commit()
        flash("تمت إضافة المقال بنجاح!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("new_article.html", form=form)


# ----------------------------
# ➕ تعديل مقال (مع رفع صورة)
# ----------------------------
@main.route("/edit-article/<int:article_id>", methods=["GET", "POST"])
def edit_article(article_id):
    if "admin" not in session:
        abort(404)

    article = Article.query.get_or_404(article_id)

    # في حالة GET نستخدم obj=article
    if request.method == "GET":
        form = ArticleForm(obj=article)
        form.related_articles.choices = [
            (a.id, a.title) for a in Article.query.all() if a.id != article.id
        ]
        form.related_articles.data = [a.id for a in article.related]
        form.tags.data = ", ".join([t.name for t in article.tags])
        form.author.choices = [(a.id, a.name) for a in Author.query.all()]
        form.author.data = article.author_id
    else:
        form = ArticleForm()
        form.related_articles.choices = [
            (a.id, a.title) for a in Article.query.all() if a.id != article.id
        ]
        form.author.choices = [(a.id, a.name) for a in Author.query.all()]

    if form.validate_on_submit():
        article.title = form.title.data
        article.content = form.content.data
        article.category = form.category.data
        article.is_published = form.is_published.data
        article.author_id = form.author.data

        if form.remove_image.data and article.image_path:
            image_path = os.path.join(
                current_app.root_path, "..", "static", "uploads", article.image_path
            )
            if os.path.exists(image_path):
                os.remove(image_path)
            article.image_path = None

        if form.image.data:
            image = form.image.data
            image_filename = secure_filename(image.filename)
            upload_folder = os.path.abspath(
                os.path.join(current_app.root_path, "..", "static", "uploads")
            )
            os.makedirs(upload_folder, exist_ok=True)
            saved_path = os.path.join(upload_folder, image_filename)
            image.save(saved_path)
            article.image_path = image_filename
        elif form.image_url.data:
            article.image_path = form.image_url.data

        # إعادة توليد السُّلَج بشكل فريد
        slug = generate_slug(form.title.data)
        existing_slug = Article.query.filter_by(slug=slug).first()
        counter = 1
        original_slug = slug
        while existing_slug and existing_slug.id != article.id:
            slug = f"{original_slug}-{counter}"
            existing_slug = Article.query.filter_by(slug=slug).first()
            counter += 1
        article.slug = slug

        # تحديث المقالات المرتبطة
        article.related = Article.query.filter(
            Article.id.in_(form.related_articles.data)
        ).all()

        # تحديث الكلمات المفتاحية
        tag_names = [t.strip() for t in form.tags.data.split(",") if t.strip()]
        tags = []
        for name in tag_names:
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name)
                db.session.add(tag)
            tags.append(tag)
        article.tags = tags

        db.session.commit()
        flash("تم تعديل المقال بنجاح!", "success")
        return redirect(url_for("main.article_detail", slug=article.slug))

    return render_template("edit_article.html", form=form, article=article)


@main.route("/upload_image", methods=["POST"])
def upload_image():
    if "admin" not in session:
        return jsonify({"success": False, "error": "غير مصرح"})

    if "image" not in request.files:
        return jsonify({"success": False, "error": "لا يوجد ملف صورة"})

    image = request.files["image"]
    if image.filename == "":
        return jsonify({"success": False, "error": "اسم الملف فارغ"})

    filename = secure_filename(image.filename)
    upload_folder = os.path.abspath(
        os.path.join(current_app.root_path, "..", "static", "uploads")
    )
    os.makedirs(upload_folder, exist_ok=True)
    saved_path = os.path.join(upload_folder, filename)
    image.save(saved_path)

    url = url_for("static", filename=f"uploads/{filename}", _external=True)
    return jsonify({"success": True, "url": url})


# ----------------------------
# ✏️ حذف مقال
# ----------------------------
@main.route("/delete-article/<int:article_id>", methods=["POST"])
def delete_article(article_id):
    if "admin" not in session:
        abort(404)

    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    flash("تم حذف المقال بنجاح ✅", "success")  # ✅ أضفنا النوع
    return redirect(url_for("main.dashboard"))


# ----------------------------
# ✏️ تصنيف مقال (مع Pagination)
# ----------------------------
@main.route("/category/<string:category_name>")
def category(category_name):
    page = request.args.get("page", 1, type=int)
    per_page = 6

    pagination = (
        Article.query.filter_by(category=category_name, is_published=True)
        .order_by(Article.date_posted.desc())
        .paginate(page=page, per_page=per_page)
    )

    articles = pagination.items

    # 🟦 جهّزنا عدد التعليقات مع كل مقال
    articles_with_comments = [
        {"article": article, "comment_count": len(article.comments)}
        for article in articles
    ]

    return render_template(
        "category.html",
        articles_with_comments=articles_with_comments,
        category=category_name,
        pagination=pagination,
    )


# ----------------------------
# ✏️ بحث كل المقالات
# ----------------------------
@main.route("/search")
def search():
    query = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "").strip()
    sort_order = request.args.get("sort", "newest").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 6

    filters = [
        Article.is_published == True,
        (Article.title.ilike(f"%{query}%") |
         Article.content.ilike(f"%{query}%")),
    ]

    if category_filter:
        filters.append(Article.category == category_filter)

    # 🧠 عمل استعلام أساسي مع عد التعليقات
    articles_query = (
        db.session.query(Article, func.count(
            Comment.id).label("comment_count"))
        .outerjoin(Comment, Comment.article_id == Article.id)
        .filter(*filters)
        .group_by(Article.id)
    )

    # ✅ ترتيب النتائج
    if sort_order == "views":
        articles_query = articles_query.order_by(Article.views.desc())
    else:
        articles_query = articles_query.order_by(Article.date_posted.desc())

    # ⏱️ لحساب وقت البحث
    from time import time

    start_time = time()

    pagination = articles_query.paginate(page=page, per_page=per_page)
    results = pagination.items
    search_time = round(time() - start_time, 3)

    # ✅ لو الطلب Ajax نرجع JSON فقط
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "articles": [
                    {
                        "title": article.title,
                        "slug": article.slug,
                        "category": article.category,
                        "views": article.views,
                        "comment_count": comment_count,
                        "image_path": article.image_path,
                        "content": article.content[:100]
                        + ("..." if len(article.content) > 100 else ""),
                        "date_posted": article.date_posted.strftime("%Y-%m-%d %H:%M"),
                    }
                    for article, comment_count in results
                ],
                "has_next": pagination.has_next,
            }
        )

    # ✅ التصنيفات
    categories = db.session.query(Article.category).distinct().all()
    categories = [c[0] for c in categories]

    return render_template(
        "search.html",
        articles=[
            {"article": article, "comment_count": comment_count}
            for article, comment_count in results
        ],
        query=query,
        category_filter=category_filter,
        sort_order=sort_order,
        categories=categories,
        results_count=pagination.total,
        search_time=search_time,
        pagination=pagination,
    )


# في نهاية ملف routes.py
@main.before_request
def restrict_direct_admin_urls():
    protected_routes = [
        "/admin-panel-38tmujf",
        "/new-article-93kfjq",
        "/edit-article",
        "/delete-article",
        "/delete_all_articles_secure",
        "/delete_all_comments_secure",
        "/article-comments-secure",
    ]
    if (
        any(request.path.startswith(p) for p in protected_routes)
        and "admin" not in session
    ):
        abort(404)


@main.route("/sitemap.xml", methods=["GET"])
def sitemap():
    base_url = "https://tecbamin.com"  # غيّره إلى دومينك الحقيقي
    urlset = Element(
        "urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # ✅ الصفحة الرئيسية
    url = SubElement(urlset, "url")
    SubElement(url, "loc").text = base_url + "/"
    SubElement(url, "changefreq").text = "daily"
    SubElement(url, "priority").text = "1.0"

    # ✅ المقالات المنشورة
    articles = Article.query.filter_by(is_published=True).all()
    for article in articles:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = base_url + "/article/" + article.slug
        SubElement(url, "lastmod").text = article.date_posted.strftime(
            "%Y-%m-%d")
        SubElement(url, "changefreq").text = "weekly"
        SubElement(url, "priority").text = "0.8"

    # ✅ التصنيفات (categories)
    categories = set(a.category for a in articles if a.category)
    for cat in categories:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = base_url + "/category/" + cat
        SubElement(url, "changefreq").text = "weekly"
        SubElement(url, "priority").text = "0.6"

    # ✅ التاجز (Tags)
    tags = Tag.query.all()
    for tag in tags:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = base_url + "/tag/" + tag.name
        SubElement(url, "changefreq").text = "weekly"
        SubElement(url, "priority").text = "0.5"

    xml_data = tostring(urlset, encoding="utf-8", method="xml")
    return Response(xml_data, mimetype="application/xml")


@main.route("/robots.txt")
def robots_txt():
    return send_from_directory(current_app.static_folder, "robots.txt")


# ----------------------------
# ✅ راوت لتجربة الخطأ 500
@main.route("/test500")
def test_500():
    abort(500)  # أو: raise Exception("تجربة خطأ 500")
