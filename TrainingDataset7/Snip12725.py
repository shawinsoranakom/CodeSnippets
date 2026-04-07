def __init__(self, initlist=None, error_class=None, renderer=None, field_id=None):
        super().__init__(initlist)

        if error_class is None:
            self.error_class = "errorlist"
        else:
            self.error_class = "errorlist {}".format(error_class)
        self.renderer = renderer or get_default_renderer()
        self.field_id = field_id