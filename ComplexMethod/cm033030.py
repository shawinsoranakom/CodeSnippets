def _build_query_with_time_filter(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> str:
        """Build the query with optional time filtering for incremental sync."""
        if not self.query:
            return ""  # Will be handled by table discovery
        base_query = self.query.rstrip(";")

        if not self.timestamp_column or (start is None and end is None):
            return base_query

        has_where = "where" in base_query.lower()
        connector = " AND" if has_where else " WHERE"

        time_conditions = []
        if start is not None:
            if self.db_type == DatabaseType.MYSQL:
                time_conditions.append(f"{self.timestamp_column} > '{start.strftime('%Y-%m-%d %H:%M:%S')}'")
            else:
                time_conditions.append(f"{self.timestamp_column} > '{start.isoformat()}'")

        if end is not None:
            if self.db_type == DatabaseType.MYSQL:
                time_conditions.append(f"{self.timestamp_column} <= '{end.strftime('%Y-%m-%d %H:%M:%S')}'")
            else:
                time_conditions.append(f"{self.timestamp_column} <= '{end.isoformat()}'")

        if time_conditions:
            return f"{base_query}{connector} {' AND '.join(time_conditions)}"

        return base_query