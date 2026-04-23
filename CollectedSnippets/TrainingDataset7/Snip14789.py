def __init__(self, request, exc_type, exc_value, tb, is_email=False):
        self.request = request
        self.filter = get_exception_reporter_filter(self.request)
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.tb = tb
        self.is_email = is_email

        self.template_info = getattr(self.exc_value, "template_debug", None)
        self.template_does_not_exist = False
        self.postmortem = None