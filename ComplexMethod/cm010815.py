def _compare_values(path: str, old_val: Any, new_val: Any) -> None:
                """Recursively compare values, handling containers."""
                # Same object, no change
                if old_val is new_val:
                    return

                if old_val is None or new_val is None:
                    if isinstance(new_val, torch.Tensor):
                        assigned_tensor_attributes.append(path)
                    return

                # Check if it's a tensor that was reassigned
                if isinstance(new_val, torch.Tensor):
                    assigned_tensor_attributes.append(path)
                    return

                # Handle dict containers
                if isinstance(old_val, dict) and isinstance(new_val, dict):
                    all_keys = set(old_val.keys()) | set(new_val.keys())
                    for key in all_keys:
                        old_item = old_val.get(key)
                        new_item = new_val.get(key)
                        _compare_values(f"{path}[{key!r}]", old_item, new_item)
                    return

                # Handle list/tuple containers
                if isinstance(old_val, (list, tuple)) and isinstance(
                    new_val, (list, tuple)
                ):
                    # Different lengths = mutation happened
                    max_len = max(len(old_val), len(new_val))
                    for i in range(max_len):
                        old_item = old_val[i] if i < len(old_val) else None
                        new_item = new_val[i] if i < len(new_val) else None
                        _compare_values(f"{path}[{i}]", old_item, new_item)
                    return