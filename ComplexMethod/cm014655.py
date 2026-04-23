def test_public_api_surface(self):
        non_back_compat_objects = {}

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

        check_symbols_have_bc_designation(torch.fx, set())
        check_symbols_have_bc_designation(torch.fx.passes, set())

        non_back_compat_strs = [
            torch.typename(obj) for obj in non_back_compat_objects
        ]
        # Only want objects in torch.fx
        non_back_compat_strs = [
            s
            for s in non_back_compat_strs
            if s.startswith("torch.fx") and not s.startswith("torch.fx.experimental")
        ]
        # Only want objects in public namespaces
        non_back_compat_strs = [
            s
            for s in non_back_compat_strs
            if all(not atom.startswith("_") for atom in s.split("."))
        ]
        non_back_compat_strs.sort()

        if len(non_back_compat_strs) != 0:
            raise AssertionError(
                f"Public FX API(s) {non_back_compat_strs} introduced but not given a "
                f"backwards-compatibility classification! Please decorate these "
                f"API(s) with `@torch.fx._compatibility.compatibility` to specify "
                f"BC guarantees."
            )