def _view_wrapper(request, *args, **kwargs):
                    result = _pre_process_request(request, *args, **kwargs)
                    if result is not None:
                        return result

                    try:
                        response = view_func(request, *args, **kwargs)
                    except Exception as e:
                        result = _process_exception(request, e)
                        if result is not None:
                            return result

                    return _post_process_request(request, response)