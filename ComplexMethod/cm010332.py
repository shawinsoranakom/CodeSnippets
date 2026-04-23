def _exporter_context(*args, **kwargs):  # type: ignore[no-untyped-def]
            import torch.export._wrapper_utils

            model: torch.nn.Module
            if not isinstance(fn, torch.nn.Module):
                model = torch.export._wrapper_utils._WrapperModule(fn)
            else:
                model = fn

            for k, v in specs.items():
                try:
                    if isinstance(fn, torch.nn.Module):
                        dynamic_shapes = v(fn, *args, **kwargs)  # type: ignore[arg-type]
                    else:
                        # pyrefly: ignore [invalid-param-spec]
                        dynamic_shapes = v(*args, **kwargs)
                except AssertionError:
                    continue
                if k not in overloads:
                    ep = torch.export.export(
                        model, args, kwargs, dynamic_shapes=dynamic_shapes
                    )
                    overloads[k] = ep
                ep = overloads[k]
                return ep.module()(*args, **kwargs)

            if fallback == "error":
                raise RuntimeError(
                    f"Exporter: Cannot export fallback {fn} when fallback policy is set to 'error',"
                    + "please specify an overload or adjust the fallback policy."
                )
            elif fallback == "once":
                if len(fallbacks) > 0:
                    raise RuntimeError(
                        f"Exporter: Cannot export {fn} more than once, "
                        + "please specify an overload or adjust the fallback policy."
                    )
            else:
                raise RuntimeError(f"Unknown fallback policy: {fallback}")
            ep = torch.export.export(model, args, kwargs)

            fallbacks.append(ep)
            return ep.module()(*args, **kwargs)