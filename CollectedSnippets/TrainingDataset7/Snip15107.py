def build_tbody_html(obj, href, field_name, extra_fields):
    return (
        "<tbody><tr>"
        '<td class="action-checkbox">'
        '<input type="checkbox" name="_selected_action" value="{}" '
        'class="action-select" aria-label="Select this object for an action - {}"></td>'
        '<th class="field-name"><a href="{}">{}</a></th>'
        "{}</tr></tbody>"
    ).format(obj.pk, str(obj), href, field_name, extra_fields)