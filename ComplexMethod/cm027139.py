def get_many(
        self, entity_ids: Iterable[str], session: Session, from_recorder: bool
    ) -> dict[str, int | None]:
        """Resolve entity_id to metadata_id.

        This call is not thread-safe after startup since
        purge can remove all references to an entity_id.

        When calling this method from the recorder thread, set
        from_recorder to True to ensure any missing entity_ids
        are added to the cache.
        """
        results: dict[str, int | None] = {}
        missing: list[str] = []
        for entity_id in entity_ids:
            if (metadata_id := self._id_map.get(entity_id)) is None:
                missing.append(entity_id)

            results[entity_id] = metadata_id

        if not missing:
            return results

        # Only update the cache if we are in the recorder thread
        # or the recorder event loop has not started yet since
        # there is a chance that we could have just deleted all
        # instances of an entity_id from the database via purge
        # and we do not want to add it back to the cache from another
        # thread (history query).
        update_cache = from_recorder or not self._did_first_load

        with session.no_autoflush:
            for missing_chunk in chunked_or_all(missing, self.recorder.max_bind_vars):
                for metadata_id, entity_id in execute_stmt_lambda_element(
                    session, find_states_metadata_ids(missing_chunk)
                ):
                    metadata_id = cast(int, metadata_id)
                    results[entity_id] = metadata_id

                    if update_cache:
                        self._id_map[entity_id] = metadata_id

        return results