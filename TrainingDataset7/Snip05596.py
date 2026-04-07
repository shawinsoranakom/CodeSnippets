def __init__(self, request, params, model, model_admin):
        self.request = request
        # This dictionary will eventually contain the request's query string
        # parameters actually used by this filter.
        self.used_parameters = {}
        if self.title is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify a 'title'."
                % self.__class__.__name__
            )