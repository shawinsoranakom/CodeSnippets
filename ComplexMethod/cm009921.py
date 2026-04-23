async def aupdate(
        self,
        keys: Sequence[str],
        *,
        group_ids: Sequence[str | None] | None = None,
        time_at_least: float | None = None,
    ) -> None:
        """Upsert records into the SQLite database."""
        if group_ids is None:
            group_ids = [None] * len(keys)

        if len(keys) != len(group_ids):
            msg = (
                f"Number of keys ({len(keys)}) does not match number of "
                f"group_ids ({len(group_ids)})"
            )
            raise ValueError(msg)

        # Get the current time from the server.
        # This makes an extra round trip to the server, should not be a big deal
        # if the batch size is large enough.
        # Getting the time here helps us compare it against the time_at_least
        # and raise an error if there is a time sync issue.
        # Here, we're just being extra careful to minimize the chance of
        # data loss due to incorrectly deleting records.
        update_time = await self.aget_time()

        if time_at_least and update_time < time_at_least:
            # Safeguard against time sync issues
            msg = f"Time sync issue: {update_time} < {time_at_least}"
            raise AssertionError(msg)

        records_to_upsert = [
            {
                "key": key,
                "namespace": self.namespace,
                "updated_at": update_time,
                "group_id": group_id,
            }
            for key, group_id in zip(keys, group_ids, strict=False)
        ]

        async with self._amake_session() as session:
            if self.dialect == "sqlite":
                from sqlalchemy.dialects.sqlite import Insert as SqliteInsertType
                from sqlalchemy.dialects.sqlite import insert as sqlite_insert

                # Note: uses SQLite insert to make on_conflict_do_update work.
                # This code needs to be generalized a bit to work with more dialects.
                sqlite_insert_stmt: SqliteInsertType = sqlite_insert(
                    UpsertionRecord,
                ).values(records_to_upsert)
                stmt = sqlite_insert_stmt.on_conflict_do_update(
                    [UpsertionRecord.key, UpsertionRecord.namespace],
                    set_={
                        "updated_at": sqlite_insert_stmt.excluded.updated_at,
                        "group_id": sqlite_insert_stmt.excluded.group_id,
                    },
                )
            elif self.dialect == "postgresql":
                from sqlalchemy.dialects.postgresql import Insert as PgInsertType
                from sqlalchemy.dialects.postgresql import insert as pg_insert

                # Note: uses SQLite insert to make on_conflict_do_update work.
                # This code needs to be generalized a bit to work with more dialects.
                pg_insert_stmt: PgInsertType = pg_insert(UpsertionRecord).values(
                    records_to_upsert,
                )
                stmt = pg_insert_stmt.on_conflict_do_update(  # type: ignore[assignment]
                    constraint="uix_key_namespace",  # Name of constraint
                    set_={
                        "updated_at": pg_insert_stmt.excluded.updated_at,
                        "group_id": pg_insert_stmt.excluded.group_id,
                    },
                )
            else:
                msg = f"Unsupported dialect {self.dialect}"
                raise NotImplementedError(msg)

            await session.execute(stmt)
            await session.commit()