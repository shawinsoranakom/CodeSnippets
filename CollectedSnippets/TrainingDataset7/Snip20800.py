def get_request(self, token=CSRF_TOKEN):
        request = HttpRequest()
        request.method = "POST"
        if token:
            request.POST["csrfmiddlewaretoken"] = token
            request.COOKIES[settings.CSRF_COOKIE_NAME] = token
        return request