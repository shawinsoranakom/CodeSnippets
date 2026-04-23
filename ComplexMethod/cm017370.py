def can_migrate(self, connection):
        """
        Return True if the model can/should be migrated on the `connection`.
        `connection` can be either a real connection or a connection alias.
        """
        if self.proxy or self.swapped or not self.managed:
            return False
        if isinstance(connection, str):
            connection = connections[connection]
        if self.required_db_vendor:
            return self.required_db_vendor == connection.vendor
        if self.required_db_features:
            return all(
                getattr(connection.features, feat, False)
                for feat in self.required_db_features
            )
        return True