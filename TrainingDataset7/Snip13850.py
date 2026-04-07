def __enter__(self):
        template_rendered.connect(self.on_template_render)
        return self