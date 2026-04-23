def _needs_inductor_compile(node: torch.fx.Node) -> bool:
    # TODO: maybe we could change to check
    # node.meta.get("partitioner_tag") != "is_forward"
    # if the tag is relibable
    return bool(
        (
            node.op not in ("placeholder", "output")
            and hasattr(node, "meta")
            and node.meta.get("custom", None)
            and node.meta["custom"].get("nested_region_config", None)
            and node.meta["custom"]["nested_region_config"].fw_compiler
            and node.meta.get("partitioner_tag") != "is_backward"
        )
        or (
            node.op not in ("placeholder", "output")
            and hasattr(node, "meta")
            and node.meta.get("custom", None)
            and node.meta["custom"].get("nested_region_config", None)
            and node.meta["custom"]["nested_region_config"].bw_compiler
            and node.meta.get("partitioner_tag") == "is_backward"
        )
    )