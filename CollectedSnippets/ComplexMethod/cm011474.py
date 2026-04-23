def _prepare_out_fn(self, outputs, device_mesh):
        prepared_outputs = []
        if not isinstance(outputs, tuple):
            outputs = (outputs,)
        if len(outputs) != len(self.output_layouts):
            raise ValueError(
                "module outputs and output_layouts should have same length!"
            )

        for out, out_layout, desired_out_layout in zip(
            outputs, self.output_layouts, self.desired_output_layouts
        ):
            if out_layout is not None:
                if isinstance(out, DTensor):
                    # TODO: re-enable the check once we fix the compile path
                    # assert out.placements[0] == out_layout
                    dt_out = out
                else:
                    dt_out = DTensor.from_local(
                        out, device_mesh, (out_layout,), run_check=False
                    )

                if out_layout != desired_out_layout:
                    dt_out = dt_out.redistribute(placements=(desired_out_layout,))
                prepared_outputs.append(
                    dt_out.to_local() if self.use_local_output else dt_out
                )
            else:
                prepared_outputs.append(out)
        if len(prepared_outputs) == 1:
            return prepared_outputs[0]
        else:
            return tuple(prepared_outputs)