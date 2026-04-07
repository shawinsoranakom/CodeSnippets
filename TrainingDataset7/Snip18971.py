def error_output(self, environ, start_response):
        super().error_output(environ, start_response)
        return ["\n".join(traceback.format_exception(*sys.exc_info()))]