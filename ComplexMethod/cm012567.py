def aliases(self) -> Iterator[tuple[str, str]]:
        for inplaced in unique(self.inplace_buffers.values()):
            if isinstance(inplaced, RemovedArg):
                continue
            for other in inplaced.other_names:
                if (
                    other in V.graph.inplaced_to_remove
                    or other in V.kernel.inplaced_to_remove
                ):
                    continue
                if other in self.input_buffers:
                    yield self.input_buffers[other], inplaced.inner_name
                if other in self.output_buffers:
                    yield cast(str, self.output_buffers[other]), inplaced.inner_name