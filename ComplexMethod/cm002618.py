def wrapped_forward(*inps, **kws):
            if _is_rank_zero():
                dict_inputs = {"args": inps, "kwargs": kws}
                dict_inputs = {k: dict_inputs[k] for k in dict_inputs if len(dict_inputs[k]) > 0}
                node = {
                    "module_path": full_path,
                    "inputs": _serialize_io(
                        dict_inputs,
                        debug_path=debug_path,
                        use_repr=use_repr,
                        path_to_value=f"{full_path}_inputs",
                    ),
                    "outputs": None,
                    "children": [],
                }
                model._debugger_model_call_stack.append(node)
            with torch.no_grad():
                out = orig_forward(*inps, **kws)

            if _is_rank_zero():
                if sum(1 for _ in module.named_children()) > 0:
                    node["outputs"] = None
                else:
                    node["outputs"] = _serialize_io(
                        out,
                        debug_path=debug_path,
                        use_repr=use_repr,
                        path_to_value=f"{full_path}_outputs",
                    )

                finished = model._debugger_model_call_stack.pop()
                # prune empty vertices here as well (mostly empty children nodes)
                if not finished["children"]:
                    finished.pop("children")

                if model._debugger_model_call_stack:
                    model._debugger_model_call_stack[-1]["children"].append(finished)
            return out