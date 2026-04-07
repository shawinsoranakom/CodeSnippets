def is_templatized(self):
        if self.domain == "django":
            file_ext = os.path.splitext(self.translatable.file)[1]
            return file_ext != ".py"
        return False