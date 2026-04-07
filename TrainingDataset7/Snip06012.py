def strip_p_tags(value):
    return mark_safe(value.replace("<p>", "").replace("</p>", ""))