def list_keys(
        self,
        *,
        before: float | None = None,
        after: float | None = None,
        group_ids: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> list[str]:
        """List records in the database based on the provided filters.

        Args:
            before: Filter to list records updated before this time.

            after: Filter to list records updated after this time.

            group_ids: Filter to list records with specific group IDs.

            limit: optional limit on the number of records to return.


        Returns:
            A list of keys for the matching records.
        """
        result = []
        for key, data in self.records.items():
            if before and data["updated_at"] >= before:
                continue
            if after and data["updated_at"] <= after:
                continue
            if group_ids and data["group_id"] not in group_ids:
                continue
            result.append(key)
        if limit:
            return result[:limit]
        return result