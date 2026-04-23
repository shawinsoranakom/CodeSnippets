def get_context(self):
        raise NotImplementedError(
            "Subclasses of RenderableMixin must provide a get_context() method."
        )