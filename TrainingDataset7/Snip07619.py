def is_too_large_for_cookie(data):
                return data and len(cookie.value_encode(data)[1]) > self.max_cookie_size