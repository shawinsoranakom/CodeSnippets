def __init__(self, http_error, message):
        super(GalaxyError, self).__init__(message)
        self.http_code = http_error.code
        self.url = http_error.geturl()

        try:
            http_msg = to_text(http_error.read())
            err_info = json.loads(http_msg)
        except (AttributeError, ValueError):
            err_info = {}

        url_split = self.url.split('/')
        if 'v3' in url_split:
            errors = err_info.get('errors', [])
            if not errors:
                errors = [{}]  # Defaults are set below, we just need to make sure 1 error is present.

            message_lines = []
            for error in errors:
                error_msg = error.get('detail') or error.get('title') or http_error.reason
                error_code = error.get('code') or 'Unknown'
                message_line = u"(HTTP Code: %d, Message: %s Code: %s)" % (self.http_code, error_msg, error_code)
                message_lines.append(message_line)

            full_error_msg = "%s %s" % (message, ', '.join(message_lines))
        else:
            # v1 and unknown API endpoints
            galaxy_msg = err_info.get('default', http_error.reason)
            full_error_msg = u"%s (HTTP Code: %d, Message: %s)" % (message, self.http_code, galaxy_msg)

        self.message = to_native(full_error_msg)