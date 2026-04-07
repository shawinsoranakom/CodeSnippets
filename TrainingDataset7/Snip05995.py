def get_url(self):
        return reverse(self.url_name % self.admin_site.name)