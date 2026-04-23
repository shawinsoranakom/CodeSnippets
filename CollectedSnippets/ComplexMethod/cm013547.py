def go(x: Any) -> str | None:
            if isinstance(x, torch.Tensor):
                for y in x.size():
                    go(y)
                for y in x.stride():
                    go(y)
                go(x.storage_offset())
                return (
                    f"Tensor(shape: {x.size()}, "
                    f"stride: {x.stride()}, "
                    f"storage_offset: {x.storage_offset()})"
                )
            elif isinstance(x, (SymBool, SymInt, SymFloat)):
                for s in x.node.expr.free_symbols:
                    if str(s) in frame_symbols:  # type: ignore[operator]
                        continue
                    if s in self.var_to_sources:
                        frame_symbols[str(s)] = self.var_to_sources[s][0].name  # type: ignore[assignment]
                return str(x)
            return None