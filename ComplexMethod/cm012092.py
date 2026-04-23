def _check_for_hop(gm: torch.fx.GraphModule) -> None:
        for module in gm.modules():
            if not isinstance(module, torch.fx.GraphModule):
                continue
            for node in module.graph.nodes:
                if (
                    isinstance(node.target, torch._ops.HigherOrderOperator)
                    and not node.target.cacheable()
                ):
                    raise BypassFxGraphCache(
                        f"Can't cache HigherOrderOperator: {node.target.name()}"
                    )
                # TODO: this check is broken in two ways:
                # 1. FX uses "get_attr" (with underscore), not "getattr"
                # 2. It only checks for ScriptObject, not FakeScriptObject
                # Fixing it would also bypass AOTAutogradCache (which calls
                # _check_can_cache), so we'd need to decouple the two first.
                if node.op == "getattr" and isinstance(
                    getattr(gm, node.target), torch._C.ScriptObject
                ):
                    raise BypassFxGraphCache("Can't cache torchbind objects")