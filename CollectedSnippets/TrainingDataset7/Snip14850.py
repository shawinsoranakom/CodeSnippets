def inner(request, *args, **kwargs):
                response, res_etag, res_last_modified = _pre_process_request(
                    request, *args, **kwargs
                )
                if response is None:
                    response = func(request, *args, **kwargs)
                _post_process_request(request, response, res_etag, res_last_modified)
                return response