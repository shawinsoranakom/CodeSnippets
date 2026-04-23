def _df_traversal(
            event: _ProfilerEvent, curr_node: _ModuleTreeNode | None = None
        ):
            # For the tensor parallel case for now only look at task 1
            if event.start_tid != 1:
                return

            if event_has_module(event):
                node = _ModuleTreeNode(event=event, parent=curr_node)
                if curr_node:
                    curr_node.children.append(node)
                else:
                    self._module_tree.append(node)
                curr_node = node

            is_leaf = event.children is None or len(event.children) == 0
            if is_leaf and curr_node:
                node = _ModuleTreeNode(
                    event=event,
                    parent=curr_node,
                    trace=event_torch_op_stack_trace(
                        event, until=lambda x: event_has_module(x)
                    ),
                )
                curr_node.children.append(node)
                curr_node = node

            for child in event.children:
                _df_traversal(child, curr_node)