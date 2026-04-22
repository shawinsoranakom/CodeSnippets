def tracking_branch(self):
        if not self.is_valid():
            return None

        if self.is_head_detached:
            return None

        return self.repo.active_branch.tracking_branch()