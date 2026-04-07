def set_response_etag(response):
    if not response.streaming and response.content:
        response.headers["ETag"] = quote_etag(
            md5(response.content, usedforsecurity=False).hexdigest(),
        )
    return response