async def _generate(self, task: dict):
        # Gmail sync reuses the generic LoadConnector/PollConnector interface
        # implemented by common.data_source.gmail_connector.GmailConnector.
        #
        # Config expectations (self.conf):
        #   credentials: Gmail / Workspace OAuth JSON (with primary admin email)
        #   batch_size:  optional, defaults to INDEX_BATCH_SIZE
        batch_size = self.conf.get("batch_size", INDEX_BATCH_SIZE)

        self.connector = GmailConnector(batch_size=batch_size)

        credentials = self.conf.get("credentials")
        if not credentials:
            raise ValueError("Gmail connector is missing credentials.")

        new_credentials = self.connector.load_credentials(credentials)
        if new_credentials:
            # Persist rotated / refreshed credentials back to connector config
            try:
                updated_conf = copy.deepcopy(self.conf)
                updated_conf["credentials"] = new_credentials
                ConnectorService.update_by_id(task["connector_id"], {"config": updated_conf})
                self.conf = updated_conf
                logging.info(
                    "Persisted refreshed Gmail credentials for connector %s",
                    task["connector_id"],
                )
            except Exception:
                logging.exception(
                    "Failed to persist refreshed Gmail credentials for connector %s",
                    task["connector_id"],
                )

        # Decide between full reindex and incremental polling by time range.
        if task["reindex"] == "1" or not task.get("poll_range_start"):
            start_time = None
            end_time = None
            _begin_info = "totally"
            document_generator = self.connector.load_from_state()
        else:
            poll_start = task["poll_range_start"]
            # Defensive: if poll_start is somehow None, fall back to full load
            if poll_start is None:
                start_time = None
                end_time = None
                _begin_info = "totally"
                document_generator = self.connector.load_from_state()
            else:
                start_time = poll_start.timestamp()
                end_time = datetime.now(timezone.utc).timestamp()
                _begin_info = f"from {poll_start}"
                document_generator = self.connector.poll_source(start_time, end_time)

        try:
            admin_email = self.connector.primary_admin_email
        except RuntimeError:
            admin_email = "unknown"
        self.log_connection("Gmail", f"as {admin_email}", task)
        return document_generator