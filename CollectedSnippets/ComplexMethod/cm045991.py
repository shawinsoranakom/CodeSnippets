def health_payload(self) -> tuple[bool, dict[str, Any]]:
        servers = [server.snapshot() for server in self.servers]
        healthy_servers = [server for server in self.servers if server.healthy]
        payload = {
            "status": "healthy" if healthy_servers else "unhealthy",
            "version": __version__,
            "protocol_version": API_PROTOCOL_VERSION,
            "queued_tasks": sum(server.queued_tasks for server in self.servers),
            "processing_tasks": sum(server.processing_tasks for server in self.servers),
            "completed_tasks": sum(server.completed_tasks for server in self.servers),
            "failed_tasks": sum(server.failed_tasks for server in self.servers),
            "max_concurrent_requests": sum(
                server.max_concurrent_requests for server in healthy_servers
            ),
            "processing_window_size": min(
                (server.processing_window_size for server in healthy_servers),
                default=MIN_HEALTHY_PROCESSING_WINDOW_SIZE,
            ),
            "servers": servers,
        }
        if not healthy_servers:
            payload["error"] = "No healthy upstream MinerU API servers are available"
        return bool(healthy_servers), payload