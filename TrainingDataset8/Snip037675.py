def uncommitted_files(self):
        if not self.is_valid():
            return None

        return [item.a_path for item in self.repo.index.diff(None)]