def _parse_gitlab_url(self, url: str) -> str | None:
        """Parse a GitLab URL to extract the repository path.

        Expected format: https://{domain}/{group}/{possibly_subgroup}/{repo}
        Returns the full path from group onwards (e.g., 'group/subgroup/repo' or 'group/repo')
        """
        try:
            # Remove protocol and domain
            if '://' in url:
                url = url.split('://', 1)[1]
            if '/' in url:
                path = url.split('/', 1)[1]
            else:
                return None

            # Clean up the path
            path = path.strip('/')
            if not path:
                return None

            # Split the path and remove empty parts
            path_parts = [part for part in path.split('/') if part]

            # We need at least 2 parts: group/repo
            if len(path_parts) < 2:
                return None

            # Join all parts to form the full repository path
            return '/'.join(path_parts)

        except Exception:
            return None