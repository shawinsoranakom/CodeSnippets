def custom_upload_path(self, filename):
            path = self.path or "tests"
            return "%s/%s" % (path, filename)