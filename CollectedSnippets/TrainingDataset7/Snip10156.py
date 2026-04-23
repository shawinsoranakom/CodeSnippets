def add_dependency(self, migration, child, parent, skip_validation=False):
        """
        This may create dummy nodes if they don't yet exist. If
        `skip_validation=True`, validate_consistency() should be called
        afterward.
        """
        if child not in self.nodes:
            error_message = (
                "Migration %s dependencies reference nonexistent"
                " child node %r" % (migration, child)
            )
            self.add_dummy_node(child, migration, error_message)
        if parent not in self.nodes:
            error_message = (
                "Migration %s dependencies reference nonexistent"
                " parent node %r" % (migration, parent)
            )
            self.add_dummy_node(parent, migration, error_message)
        self.node_map[child].add_parent(self.node_map[parent])
        self.node_map[parent].add_child(self.node_map[child])
        if not skip_validation:
            self.validate_consistency()