def get_buf_bytes(
                buf: ir.Buffer | ir.TensorBox | ir.TorchBindObject | None,
            ) -> int:
                if not buf:
                    return 0

                if isinstance(buf, ir.TorchBindObject):
                    return buf.get_buf_bytes()
                elif isinstance(buf.layout, MultiOutputLayout):
                    # Kind of a lazy way to get the MultiOutput nodes corresponding to
                    # a MultiOutputLayout
                    users = self.scheduler.name_to_buf[buf.get_name()].users
                    tot = 0
                    for user in users:
                        if isinstance(user.node, OutputNode):
                            continue
                        assert isinstance(user.node, BaseSchedulerNode)
                        if isinstance(user.node.node, MultiOutput):
                            for sched_buf in user.node.get_outputs():
                                tot += get_buf_bytes(sched_buf.node)
                        else:
                            # Buf is a MultiOutputLayout but not all of its
                            # users are MultiOutputs...
                            # TODO: Figure out what's going on
                            return 0
                    return tot
                elif isinstance(buf.layout, ir.NoneLayout):
                    return sum(
                        get_buf_bytes(V.graph.get_buffer(mut_name))
                        for mut_name in buf.get_mutation_names()
                    )
                else:
                    buf_elems = try_size_hint(sympy_product(buf.get_size()))
                    return get_dtype_size(buf.get_dtype()) * min(
                        buf_accessed_elems, buf_elems
                    )