async def search_sandboxes(
        self,
        page_id: str | None = None,
        limit: int = 100,
    ) -> SandboxPage:
        """Search for sandboxes."""
        try:
            # Get all containers with our prefix
            all_containers = self.docker_client.containers.list(all=True)
            sandboxes = []

            for container in all_containers:
                if container.name and container.name.startswith(
                    self.container_name_prefix
                ):
                    sandbox_info = await self._container_to_checked_sandbox_info(
                        container
                    )
                    if sandbox_info:
                        sandboxes.append(sandbox_info)

            # Sort by creation time (newest first)
            sandboxes.sort(key=lambda x: x.created_at, reverse=True)

            # Apply pagination
            start_idx = 0
            if page_id:
                try:
                    start_idx = int(page_id)
                except ValueError:
                    start_idx = 0

            end_idx = start_idx + limit
            paginated_containers = sandboxes[start_idx:end_idx]

            # Determine next page ID
            next_page_id = None
            if end_idx < len(sandboxes):
                next_page_id = str(end_idx)

            return SandboxPage(items=paginated_containers, next_page_id=next_page_id)

        except APIError:
            return SandboxPage(items=[], next_page_id=None)