def map_value(key: str, value: Any) -> Any:
            if key == "guards":
                # Transform the list of ShapeGuard into a list of expressions.
                return [g.expr for g in value]
            elif key == "deferred_runtime_asserts":
                # Transform the list of RuntimeAsserts into a list of expressions.
                return {s: [ra.expr for ra in ras] for s, ras in value.items()}
            elif key == "name_to_node":
                # Compare just the set of keys is the same.
                return set(value.keys())
            elif key in (
                "symbol_guard_counter",
                "pending_fresh_unbacked_symbols",
                "fake_tensor_cache",
            ):
                # Skip this for comparisons
                return None
            return value