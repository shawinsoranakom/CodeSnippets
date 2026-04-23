def _get_scheme(self):
        """
        Hook for subclasses like WSGIRequest to implement. Return 'http' by
        default.
        """
        return "http"