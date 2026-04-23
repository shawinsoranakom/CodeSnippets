def __init__(self, template, backend):
        self.template = template
        self.backend = backend
        self.origin = Origin(
            name=template.filename,
            template_name=template.name,
        )