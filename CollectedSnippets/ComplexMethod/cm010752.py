def materialize_arg(x: Any) -> Any:
        if isinstance(x, fx.Node) and isinstance(x.meta["val"], torch.Tensor):
            return _remove_symbols_without_guarding(x.meta["val"], fallback=4096)
        elif isinstance(x, fx.Node) and isinstance(x.meta["val"], torch.SymInt):
            return optimization_hint(x.meta["val"], fallback=4096)
        elif isinstance(x, fx.Node) and isinstance(x.meta["val"], torch.SymFloat):
            return 1.0
        elif isinstance(x, fx.Node) and isinstance(x.meta["val"], torch.SymBool):
            return True
        else:
            return x