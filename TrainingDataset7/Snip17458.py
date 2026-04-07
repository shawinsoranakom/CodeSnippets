def _get_password_reset_confirm_redirect_url(self, url):
        token = extract_token_from_url(url)
        if not token:
            return url
        # Add the token to the session
        session = self.session
        session[INTERNAL_RESET_SESSION_TOKEN] = token
        session.save()
        return url.replace(token, self.reset_url_token)