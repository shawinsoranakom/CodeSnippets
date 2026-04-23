def _flat_out_extrafields(self, nodes, out=None):
        if out is None:
            out = []
        for node in nodes:
            if (
                isinstance(node.extra_fields, _ExtraFields_PyCall)
                and node.extra_fields.optimizer
                and node.extra_fields.optimizer.parameters
            ):
                # avoiding OptInfo duplicates from iterations
                addr = node.extra_fields.optimizer.parameters[0][0].storage_data_ptr
                if not [o for o in out if addr == o.parameters[0][0].storage_data_ptr]:
                    out.append(node.extra_fields.optimizer)
            self._flat_out_extrafields(node.children, out)
        return out