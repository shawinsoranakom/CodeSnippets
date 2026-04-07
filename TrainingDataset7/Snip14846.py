def _post_process_request(request, response, res_etag, res_last_modified):
            # Set relevant headers on the response if they don't already exist
            # and if the request method is safe.
            if request.method in ("GET", "HEAD"):
                if res_last_modified and not response.has_header("Last-Modified"):
                    response.headers["Last-Modified"] = http_date(res_last_modified)
                if res_etag:
                    response.headers.setdefault("ETag", res_etag)