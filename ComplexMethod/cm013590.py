def on_node_replace(old: Node, new: str, user: Node) -> None:
            # Update node meta when replacing old node with new node
            new_node = self.name_to_node.get(new, None)

            if not new_node:
                return

            if not isinstance(new_node, Node):
                raise AssertionError(f"Expected Node, got {type(new_node)}")

            # replace hook is called once for each user of old
            # this avoids adding duplicated source nodes
            added_nodes = {s.name for s in new_node.meta.get("from_node", [])}
            if old.name in added_nodes:
                return

            action = [NodeSourceAction.REPLACE]
            if new_node.name in self.created_nodes:
                action.append(NodeSourceAction.CREATE)

            def created_this_pass(source: NodeSource) -> bool:
                return source.pass_name == self.passname and source.action == [
                    NodeSourceAction.CREATE
                ]

            # remove redundant source added on node creation
            new_from_node = new_node.meta.get("from_node", [])
            new_from_node = [
                source for source in new_from_node if not created_this_pass(source)
            ]

            # add new source
            new_node_source = NodeSource(old, self.passname, action)
            new_from_node.append(new_node_source)
            new_node.meta["from_node"] = new_from_node