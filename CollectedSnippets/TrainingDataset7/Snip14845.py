def _pre_process_request(request, *args, **kwargs):
            # Compute values (if any) for the requested resource.
            res_last_modified = None
            if last_modified_func:
                if dt := last_modified_func(request, *args, **kwargs):
                    if not timezone.is_aware(dt):
                        dt = timezone.make_aware(dt, datetime.UTC)
                    res_last_modified = int(dt.timestamp())
            # The value from etag_func() could be quoted or unquoted.
            res_etag = etag_func(request, *args, **kwargs) if etag_func else None
            res_etag = quote_etag(res_etag) if res_etag is not None else None
            response = get_conditional_response(
                request,
                etag=res_etag,
                last_modified=res_last_modified,
            )
            return response, res_etag, res_last_modified