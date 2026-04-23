def get_success_url(self):
        return self.get_redirect_url() or self.get_default_redirect_url()