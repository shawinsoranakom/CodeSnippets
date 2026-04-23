def __init__(
        self,
        form,
        name=None,
        readonly_fields=(),
        fields=(),
        classes=(),
        description=None,
        model_admin=None,
    ):
        self.form = form
        self.name, self.fields = name, fields
        self.classes = " ".join(classes)
        self.description = description
        self.model_admin = model_admin
        self.readonly_fields = readonly_fields