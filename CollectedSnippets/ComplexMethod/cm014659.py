def check_symbols_have_bc_designation(m, seen):
            if not m.__name__.startswith("torch.fx"):
                return
            if m.__name__.startswith("torch.fx.experimental"):
                return
            # It's really common for inner functions to point to random modules
            # - make sure we don't recurse into modules we've already checked.
            seen.add(m.__name__)
            for k, v in m.__dict__.items():
                if hasattr(v, "__name__") and v.__name__ in seen:
                    continue
                if v is m:
                    continue
                if k.startswith("_"):
                    continue
                if isinstance(v, types.ModuleType):
                    check_symbols_have_bc_designation(v, seen)
                elif isinstance(v, (type, types.FunctionType)):
                    if v not in _MARKED_WITH_COMPATIBILITY:
                        non_back_compat_objects.setdefault(v)