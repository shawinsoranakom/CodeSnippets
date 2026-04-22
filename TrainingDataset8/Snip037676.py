def ahead_commits(self):
        if not self.is_valid():
            return None

        try:
            remote, branch_name = self.get_tracking_branch_remote()
            remote_branch = "/".join([remote.name, branch_name])

            return list(self.repo.iter_commits(f"{remote_branch}..{branch_name}"))
        except Exception:
            return list()