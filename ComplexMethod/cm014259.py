def __str__(self) -> str:
        output = f"Graph Count: {self.graph_count}\n"
        output += f"Graph Break Count: {self.graph_break_count}\n"
        output += f"Op Count: {self.op_count}\n"

        output += "Break Reasons:\n"
        for idx, break_reason in enumerate(self.break_reasons):
            output += f"  Break Reason {idx + 1}:\n"
            output += f"    Reason: {break_reason.reason}\n"
            output += "    User Stack:\n"
            for frame_summary in break_reason.user_stack:
                output += f"      {frame_summary}\n"

        if self.ops_per_graph is not None:
            output += "Ops per Graph:\n"
            for idx, ops in enumerate(self.ops_per_graph):
                output += f"  Ops {idx + 1}:\n"
                for op in ops:
                    output += f"    {op}\n"

        if self.out_guards is not None:
            output += "Out Guards:\n"
            for i, guard in enumerate(self.out_guards):
                output += f"  Guard {i + 1}:\n"
                output += f"    {str(guard)}"

        if self.compile_times is not None:
            output += f"Compile Times: {self.compile_times}\n"
        return output