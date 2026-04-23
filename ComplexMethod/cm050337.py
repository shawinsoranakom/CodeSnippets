def build_from_stream(self, stream):
        """ Build an Asn1 tree starting from a byte string from a p7m file """

        self.clear()
        while self.offset < len(stream):

            start_offset = self.offset
            self.last_open_node = self.open_nodes_stack[-1] if self.open_nodes_stack else None

            # Read the definition and length bytes
            definition_byte, self.offset = self.consume('B', stream, self.offset)
            node_len, _bytes_read, self.offset = self.read_length(stream, self.offset)

            if definition_byte == 0 and node_len == 0 and self.open_nodes_stack:
                yield self.finalize_last_open_node()
                continue

            # Create the current Node
            self.current_node = self.create_node(definition_byte, node_len, start_offset, parent=self.parent_node)
            if not self.root:
                self.root = self.current_node

            # If not primitive, add to the stack
            if not issubclass(self.current_node.__class__, PrimitiveNode):
                self.open_nodes_stack.append(self.current_node)
                self.last_open_node = self.current_node
                self.parent_node = self.current_node
            else:
                data, self.offset = self.consume('%ss' % self.current_node.length, stream, self.offset)
                self.current_node.finalize(self.offset, data)
                yield self.current_node

            # Clear the stack of all finished nodes
            while (
                self.last_open_node
                and not self.last_open_node.finalized
                and self.last_open_node.length != '?'
                and self.last_open_node.start_offset + self.last_open_node.total_length() <= self.offset
            ):
                yield self.finalize_last_open_node()

        return self.root