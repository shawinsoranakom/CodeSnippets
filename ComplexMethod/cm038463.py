def _log_failure(
        self,
        failure_type: str,
        req_id: str | None,
        msg: str = "",
        error: Exception | None = None,
        meta: ReqMeta | None = None,
        **extra_context,
    ):
        """Log transfer failure with structured context for easier debugging."""
        context: dict[str, Any] = {
            "failure_type": failure_type,
            "request_id": req_id,
            "engine_id": self.engine_id,
        }
        if meta is None and req_id is not None:
            # Try to get metadata from in progress transfers when not provided
            meta = self._recving_metadata.get(req_id)

        if meta and meta.remote:
            context.update(
                {
                    "remote_engine_id": meta.remote.engine_id,
                    "remote_request_id": meta.remote.request_id,
                    "remote_host": meta.remote.host,
                    "remote_port": meta.remote.port,
                    "num_local_blocks": sum(
                        len(group) for group in meta.local_block_ids
                    ),
                    "num_remote_blocks": sum(
                        len(group) for group in meta.remote.block_ids
                    ),
                    "local_block_ids_sample": meta.local_block_ids[0][:10]
                    if meta.local_block_ids
                    else [],
                }
            )

        context.update(extra_context)
        if msg:
            failure_type = f"{failure_type}. {msg}"

        logger.error(
            "NIXL transfer failure: %s | Context: %s",
            failure_type,
            context,
            exc_info=error is not None,
            stacklevel=2,
        )