def is_head_detached(self):
        if not self.is_valid():
            return False

        return self.repo.head.is_detached