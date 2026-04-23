def disallowed_aggregates(self):
        disallowed_aggregates = [
            models.Extent,
            models.Extent3D,
            models.MakeLine,
            models.Union,
        ]
        is_mariadb = self.connection.mysql_is_mariadb
        if is_mariadb:
            if self.connection.mysql_version < (12, 0, 1):
                disallowed_aggregates.insert(0, models.Collect)
        return tuple(disallowed_aggregates)