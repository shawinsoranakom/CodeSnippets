def _find_active_connection_for_app(self, app_name: str) -> tuple[str, str] | None:
        """Find any ACTIVE connection for this app/user. Returns (connection_id, status) or None."""
        try:
            composio = self._build_wrapper()
            connection_list = composio.connected_accounts.list(
                user_ids=[self.entity_id], toolkit_slugs=[app_name.lower()]
            )

            if connection_list and hasattr(connection_list, "items") and connection_list.items:
                for connection in connection_list.items:
                    connection_id = getattr(connection, "id", None)
                    connection_status = getattr(connection, "status", None)
                    if connection_status == "ACTIVE" and connection_id:
                        logger.info(f"Found existing ACTIVE connection for {app_name}: {connection_id}")
                        return connection_id, connection_status

        except (ValueError, ConnectionError) as e:
            logger.error(f"Error finding active connection for {app_name}: {e}")
            return None
        else:
            return None