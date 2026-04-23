def walk(output: object, indices: list[tuple[type, int]]) -> list[TensorBox]:
            if isinstance(output, (list, tuple)):
                results: list[TensorBox] = []
                for i, item in enumerate(output):
                    results.extend(walk(item, [*indices, (type(output), i)]))
                return results
            leaf_idx = next(leaf_counter)
            if isinstance(output, torch.Tensor):
                if direct_alias_at_leaf and leaf_idx in direct_alias_at_leaf:
                    return [TensorBox.create(direct_alias_at_leaf[leaf_idx])]
                tid = id(output)
                if tid in seen_outputs:
                    return [seen_outputs[tid]]
                mo = MultiOutput(
                    FallbackKernel.tensor_to_layout(output), template_buf, indices
                )
                template_buf._multi_output_children[mo.get_name()] = mo
                if on_tensor_leaf is not None:
                    on_tensor_leaf(mo.get_name(), mo, indices, leaf_idx)
                tb = TensorBox(mo)
                seen_outputs[tid] = tb
                return [tb]
            # Non-tensor leaf (int, SymInt, None, etc.)
            if on_non_tensor_leaf is not None:
                on_non_tensor_leaf(leaf_idx)
            return []