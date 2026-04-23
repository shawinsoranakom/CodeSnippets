def _boolean_icon(field_val):
    icon_url = static(
        "admin/img/icon-%s.svg" % {True: "yes", False: "no", None: "unknown"}[field_val]
    )
    return format_html('<img src="{}" alt="{}">', icon_url, field_val)