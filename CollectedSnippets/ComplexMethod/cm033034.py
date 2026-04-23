def _iter_target_repositories(self, client: httpx.Client) -> Iterator[str]:
        """Yield repository slugs based on configuration.

        Priority:
        - repositories list
        - projects list (list repos by project key)
        - workspace (all repos)
        """
        if self._repositories:
            for slug in self._repositories:
                yield slug
            return
        if self._projects:
            for project_key in self._projects:
                for repo in list_repositories(client, self.workspace, project_key):
                    slug_val = repo.get("slug")
                    if isinstance(slug_val, str) and slug_val:
                        yield slug_val
            return
        for repo in list_repositories(client, self.workspace, None):
            slug_val = repo.get("slug")
            if isinstance(slug_val, str) and slug_val:
                yield slug_val