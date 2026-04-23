def remove_replaced_nodes(self, replacement, replaced):
        """
        Remove each of the `replaced` nodes (when they exist). Any
        dependencies that were referencing them are changed to reference the
        `replacement` node instead.
        """
        # Cast list of replaced keys to set to speed up lookup later.
        replaced = set(replaced)
        try:
            replacement_node = self.node_map[replacement]
        except KeyError as err:
            raise NodeNotFoundError(
                "Unable to find replacement node %r. It was either never added"
                " to the migration graph, or has been removed." % (replacement,),
                replacement,
            ) from err
        for replaced_key in replaced:
            self.nodes.pop(replaced_key, None)
            replaced_node = self.node_map.pop(replaced_key, None)
            if replaced_node:
                for child in replaced_node.children:
                    child.parents.remove(replaced_node)
                    # We don't want to create dependencies between the replaced
                    # node and the replacement node as this would lead to
                    # self-referencing on the replacement node at a later
                    # iteration.
                    if child.key not in replaced:
                        replacement_node.add_child(child)
                        child.add_parent(replacement_node)
                for parent in replaced_node.parents:
                    parent.children.remove(replaced_node)
                    # Again, to avoid self-referencing.
                    if parent.key not in replaced:
                        replacement_node.add_parent(parent)
                        parent.add_child(replacement_node)