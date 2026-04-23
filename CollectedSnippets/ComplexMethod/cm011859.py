def build_node_info(node: ir.IRNode) -> dict[str, str]:
            if hasattr(node, "name"):
                node_name = node.name
            else:
                node_name = ""
            node_info = {
                "name": node_name,
                "type": type(node).__name__,
            }
            try:
                layout = node.get_output_spec()
                if isinstance(layout, FixedLayout):
                    static_layout = FixedLayout(
                        layout.device,
                        dtype=layout.dtype,
                        size=V.graph.sizevars.optimization_hints(layout.size),
                        stride=V.graph.sizevars.optimization_hints(layout.stride),
                        offset=V.graph.sizevars.optimization_hint(
                            layout.offset, fallback=0
                        ),
                    )
                    node_info["layout"] = str(static_layout)
                else:
                    node_info["layout"] = str(layout)
            except Exception:
                pass
            try:
                node_info["dtype"] = str(node.get_dtype())
            except Exception:
                pass
            try:
                node_info["device"] = str(node.get_device())
            except Exception:
                pass
            try:
                node_info["stride"] = str(
                    V.graph.sizevars.optimization_hints(node.get_stride())
                )
            except Exception:
                pass
            try:
                node_info["size"] = str(
                    V.graph.sizevars.optimization_hints(node.get_size())
                )  # type: ignore[arg-type]
            except Exception:
                pass
            try:
                node_info["numel"] = str(
                    V.graph.sizevars.optimization_hint(node.get_numel())
                )
            except Exception:
                pass
            if hasattr(node, "data") and isinstance(node.data, ir.IRNode):
                node_info["data"] = build_node_info(node.data)
            return node_info