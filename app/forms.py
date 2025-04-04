from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    BooleanField,
    SubmitField,
    SelectField,
    PasswordField,
)
from wtforms.validators import DataRequired, Length, Optional, URL, Email, Length
from wtforms import SelectMultipleField


class ArticleForm(FlaskForm):
    title = StringField("عنوان المقال", validators=[DataRequired()])
    author = SelectField("كاتب المقال", coerce=int, validators=[Optional()])
    content = TextAreaField("المحتوى", validators=[DataRequired()])
    slug = StringField("رابط المقال (اختياري)")

    # ✅ المقالات المرتبطة
    related_articles = SelectMultipleField("مقالات مرتبطة", coerce=int)

    # ✅ التاجز (مفصولة بفاصلة)
    tags = StringField(
        "الكلمات المفتاحية (التاجز)", description="اكتب الكلمات مفصولة بفاصلة (،)"
    )

    # ✅ خيار حذف الصورة
    remove_image = BooleanField("حذف الصورة الحالية؟")

    # ✅ اختيار التصنيف
    category = SelectField(
        "التصنيف",
        choices=[
            ("تقنية", "تقنية"),
            ("مراجعات", "مراجعات"),
            ("ثقافة", "ثقافة"),
            ("أخبار", "أخبار"),
            ("عام", "عام"),
        ],
    )

    # ✅ النشر الفوري
    is_published = BooleanField("نشر المقال الآن؟")

    # ✅ صورة من الجهاز
    image = FileField(
        "رفع صورة من جهازك",
        validators=[FileAllowed(["jpg", "png", "jpeg"], "Images only!")],
    )

    # ✅ رابط صورة خارجي
    image_url = StringField(
        "أو ضع رابط لصورة",
        validators=[Optional(), URL(message="يجب أن يكون الرابط صحيحًا")],
    )

    # ✅ زر الحفظ
    submit = SubmitField("حفظ")


class LoginForm(FlaskForm):
    username = StringField("اسم المستخدم", validators=[DataRequired()])
    password = PasswordField("كلمة المرور", validators=[DataRequired()])
    submit = SubmitField("تسجيل الدخول")


class CommentForm(FlaskForm):
    name = StringField("الاسم", validators=[DataRequired(), Length(max=100)])
    content = TextAreaField("اكتب تعليقك", validators=[DataRequired()])
    submit = SubmitField("إرسال")


class ContactForm(FlaskForm):
    name = StringField("الاسم", validators=[DataRequired(), Length(max=100)])
    email = StringField(
        "البريد الإلكتروني", validators=[DataRequired(), Email(), Length(max=50)]
    )
    message = TextAreaField("الرسالة", validators=[
                            DataRequired(), Length(max=1000)])
    submit = SubmitField("إرسال")
