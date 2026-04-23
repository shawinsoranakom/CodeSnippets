def generate_workspace_allocation(self, ws: WorkspaceArg):
        name = ws.get_name()
        line = AllocateLine(self, ws)
        if ws.zero_mode == WorkspaceZeroMode.UNINITIALIZED:
            self.writeline(line)
        elif ws.zero_mode == WorkspaceZeroMode.ZERO_ON_CALL:
            self.writeline(line)
            self.writeline(self.make_zero_buffer(name))
        elif ws.zero_mode == WorkspaceZeroMode.ZERO_PER_GRAPH:
            prior = self.allocated_workspaces.get(name)
            if prior:
                assert isinstance(prior, AllocateLine) and isinstance(
                    prior.node, WorkspaceArg
                )
                # expand existing allocation
                prior.node = WorkspaceArg.maximum(prior.node, ws)
            else:
                self.writeline(line)
                self.writeline(self.make_zero_buffer(name))
                self.allocated_workspaces[name] = line
        else:
            raise AssertionError(ws.zero_mode)

        if config.triton.autotune_at_compile_time:
            self.kernel_autotune_calls.writeline(
                PythonWrapperCodegen.make_allocation(
                    self,
                    name,
                    ws.device,
                    ws.dtype,
                    shape=(V.graph.sizevars.optimization_hint(ws.count),),
                    stride=(1,),
                )
            )
            if ws.zero_mode != WorkspaceZeroMode.UNINITIALIZED:
                self.kernel_autotune_calls.writeline(
                    PythonWrapperCodegen.make_zero_buffer(self, name)
                )