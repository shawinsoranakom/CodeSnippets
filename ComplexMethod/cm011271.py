def _find_loss_from_output_and_spec(output_val, spec_val):
    if spec_val is False:
        return None
    if spec_val is True:
        if not isinstance(output_val, fx.Node):
            raise RuntimeError(
                f"Loss spec must specify a dynamic value but got {output_val}"
            )
        return output_val

    if isinstance(spec_val, (tuple, list)):
        if not isinstance(output_val, (tuple, list)):
            raise RuntimeError(
                f"Output value {output_val} must match type of loss specification "
                f"{spec_val}"
            )
        if len(output_val) != len(spec_val):
            raise RuntimeError(
                f"Output value {output_val} must match length of loss specification "
                f"{spec_val}"
            )
        for out, spec in zip(output_val, spec_val):
            loss_val = _find_loss_from_output_and_spec(out, spec)
            if loss_val is not None:
                return loss_val
        raise RuntimeError(f"Did not find loss value in specification {spec_val}")

    if isinstance(spec_val, dict):
        if not isinstance(output_val, dict):
            raise RuntimeError(
                f"Output value {output_val} must match type of loss specification "
                f"{spec_val}"
            )
        if set(output_val.keys()) != set(spec_val.keys()):
            raise RuntimeError(
                f"Output value {output_val} must match keys of loss specification "
                f"{spec_val}"
            )
        for k in spec_val:
            loss_val = _find_loss_from_output_and_spec(output_val[k], spec_val[k])
            if loss_val is not None:
                return loss_val
        raise RuntimeError(f"Did not find loss value in specification {spec_val}")

    raise RuntimeError(f"Unsupported type {type(spec_val)} in loss specification")