def __init__(self, form, field, readonly_fields=None, model_admin=None):
        self.form = form  # A django.forms.Form instance
        if not hasattr(field, "__iter__") or isinstance(field, str):
            self.fields = [field]
        else:
            self.fields = field
        self.has_visible_field = not all(
            field in self.form.fields and self.form.fields[field].widget.is_hidden
            for field in self.fields
        )
        self.model_admin = model_admin
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields