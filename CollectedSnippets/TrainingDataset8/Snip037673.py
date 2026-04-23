def untracked_files(self):
        if not self.is_valid():
            return None

        return self.repo.untracked_files