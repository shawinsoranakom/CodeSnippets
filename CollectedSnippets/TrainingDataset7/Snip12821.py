def __init__(self, widgets, attrs=None):
        if isinstance(widgets, dict):
            self.widgets_names = [("_%s" % name) if name else "" for name in widgets]
            widgets = widgets.values()
        else:
            self.widgets_names = ["_%s" % i for i in range(len(widgets))]
        self.widgets = [w() if isinstance(w, type) else w for w in widgets]
        super().__init__(attrs)