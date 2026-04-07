def get_migration(self, app_label, name_prefix):
        """Return the named migration or raise NodeNotFoundError."""
        return self.graph.nodes[app_label, name_prefix]