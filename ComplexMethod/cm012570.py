def remove_kernel_local_buffers(self) -> None:
        """
        Any buffers that are both created and have a last use in the
        same kernel can be removed.

        Note that V.graph.scheduler can be None when codegening triton template
        kernels.
        """
        scheduler = V.graph.scheduler
        if not scheduler:
            return
        fused_node_names = OrderedSet(
            scheduler.name_to_buf[buf].defining_op_name()
            for buf in self.store_buffer_names
            if buf in scheduler.name_to_buf
        )
        names_to_remove: OrderedSet[str] = OrderedSet()
        for name in self.store_buffer_names:
            if (
                name not in self.must_keep_buffers
                and name not in self.args.input_buffers
                and scheduler.can_buffer_be_removed_through_fusion(
                    name, fused_node_names
                )
            ):
                self.num_store -= 1
                names_to_remove.add(name)

        for name in names_to_remove:
            if name in self.args.inplace_buffers:
                buf = self.args.inplace_buffers[name]
                if isinstance(buf, RemovedArg):
                    continue
                remove = all(n in names_to_remove for n in buf.other_names)
                if remove:
                    self.remove_inplace_buffer(name)
                self.inplaced_to_remove.add(name)
            else:
                self.remove_buffer(name)