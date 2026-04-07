def _view_wrapper(*args, **kwargs):
            response = view_func(*args, **kwargs)
            response.xframe_options_exempt = True
            return response