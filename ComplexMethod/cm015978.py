def _run_and_format_data_flow(
        inputs: dict[str, torch.Tensor],
        f: Callable[..., dict[str, torch.Tensor] | None],
        indent: int = 12,
    ) -> str:
        with profile() as prof:
            outputs = f(**inputs) or {}
            gc.collect()

        memory_profile = prof._memory_profile()
        graph = memory_profile._data_flow_graph
        storage_to_id = {key.storage.ptr: key.id for key in graph._active_version}

        lines: list[str] = []
        for name, t in it.chain(inputs.items(), outputs.items()):
            lines.append(f"{name + ':':<8} T{storage_to_id[t.storage().data_ptr()]}")
            if t.grad is not None:
                grad_id = storage_to_id[t.grad.storage().data_ptr()]
                lines.append(f"{name + '.grad:':<9} T{grad_id}")

        if lines:
            lines.append("")

        for node in graph.flow_nodes:
            destroyed = {k for k, v in node._edges.items() if v.is_deletion}

            inputs: list[str] = []
            for key, (_, v) in node.inputs.items():
                inputs.append(f"T{key.id}(v{v}{'*' if key in destroyed else ''})")

            outputs = [f"T{key.id}(v{v})" for key, v in node.outputs.items()]
            if inputs or outputs:
                event_name = node._event.name.replace("torch::autograd::", "")
                lines.append(
                    f"{event_name:<25} {', '.join(inputs):<15}  ->  {', '.join(outputs)}"
                )

        return textwrap.indent("\n".join([l.rstrip() for l in lines]), " " * indent)