from datetime import datetime
import pytz


def to_egypt_time_str(utc_datetime):
    cairo_tz = pytz.timezone("Africa/Cairo")
    local_time = utc_datetime.replace(tzinfo=pytz.utc).astimezone(cairo_tz)
    return local_time.strftime("%Y-%m-%d %H:%M")


def insert_ad_after_paragraph(content, ad_html, after_paragraph=2):
    try:
        parts = content.split("</p>")
        if len(parts) > after_paragraph:
            parts[after_paragraph] += ad_html
        return "</p>".join(parts)
    except Exception:
        return content
