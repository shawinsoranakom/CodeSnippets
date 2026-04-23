def __init__(self, widget, size, **kwargs):
        self.widget = widget() if isinstance(widget, type) else widget
        self.size = size
        super().__init__(**kwargs)