def as_widget(self):
        raise NotImplementedError(
            "Subclasses of RenderableFieldMixin must provide an as_widget() method."
        )