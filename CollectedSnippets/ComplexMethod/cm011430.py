def wrap(res: object, spec: OutputSpecType) -> object:
        if isinstance(res, torch.Tensor):
            if spec is not None:
                if not isinstance(spec, DTensorSpec):
                    raise AssertionError(
                        f"output spec does not match with output! Expected DTensorSpec, got {spec}."
                    )
                # pyrefly: ignore [bad-argument-type, bad-argument-count, unexpected-keyword]
                return dtensor.DTensor(res, spec, requires_grad=res.requires_grad)
            else:
                # if output does not have a DTensorSpec due to specific ops, it must be a scalar tensor
                if res.ndim != 0:
                    raise AssertionError("output tensor should be scalar!")
                return res
        elif isinstance(res, (list, tuple)):
            if not (spec is not None and isinstance(spec, (list, tuple))):
                raise AssertionError(
                    f"output spec does not match with output! Expected list/tuple, got {spec}."
                )
            res_list = []
            for e, s in zip(res, spec):
                # pyrefly: ignore [bad-argument-type]
                res_list.append(OpDispatcher.wrap(e, s))

            return tuple(res_list) if isinstance(res, tuple) else res_list
        else:
            # if the res contains only non tensor values (i.e. int/float/none), we simply return it
            # without rewrapping to DTensor.
            return res