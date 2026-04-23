def walk(n: torch.fx.Node) -> None:
            if n.name in visited:
                return
            visited.add(n.name)
            source = get_node_source_info(n)

            if n.op == "placeholder":
                block = []
                if source:
                    block.append(f"# {source}")
                block.append(f"{n.name}: graph input ({n.target})")
                placeholder_blocks.append(block)
                return

            if n.op == "call_function" and len(op_blocks) < max_lines:
                target_name = getattr(n.target, "__name__", str(n.target))
                args_str = ", ".join(fmt_arg(a) for a in n.args)
                block = []
                if source:
                    block.append(f"# {source}")
                block.append(f"{n.name} = {target_name}({args_str})")
                op_blocks.append(block)

                for a in n.args:
                    if isinstance(a, torch.fx.Node):
                        walk(a)