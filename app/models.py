from . import db
from datetime import datetime

related_articles = db.Table(
    "related_articles",
    db.Column("article_id", db.Integer, db.ForeignKey(
        "article.id"), primary_key=True),
    db.Column("related_id", db.Integer, db.ForeignKey(
        "article.id"), primary_key=True),
)

article_tags = db.Table(
    "article_tags",
    db.Column("article_id", db.Integer, db.ForeignKey(
        "article.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(50), nullable=False, default="عام")
    views = db.Column(db.Integer, default=0)
    image_path = db.Column(db.String(100))
    author_id = db.Column(
        db.Integer, db.ForeignKey("author.id"), nullable=True)

    related = db.relationship(
        "Article",
        secondary=related_articles,
        primaryjoin=id == related_articles.c.article_id,
        secondaryjoin=id == related_articles.c.related_id,
        backref="related_to",
        lazy="dynamic",
    )

    tags = db.relationship(
        "Tag",
        secondary=article_tags,
        backref=db.backref("articles", lazy="dynamic"),
        lazy="dynamic",
    )


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    is_approved = db.Column(db.Boolean, default=False)

    article_id = db.Column(db.Integer, db.ForeignKey(
        "article.id"), nullable=False)
    article = db.relationship(
        "Article", backref=db.backref("comments", lazy=True))

    parent_id = db.Column(db.Integer, db.ForeignKey("comment.id"))
    replies = db.relationship(
        "Comment", backref=db.backref("parent", remote_side=[id]), lazy=True
    )


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    articles = db.relationship("Article", backref="author", lazy=True)
