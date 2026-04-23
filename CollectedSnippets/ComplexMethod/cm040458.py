def cond(pred, true_fn, false_fn):
    class _TrackingScope(StatelessScope):
        """StatelessScope that retains variable object references."""

        def __init__(self):
            super().__init__()
            self._var_objects = {}

        def add_update(self, update):
            variable, value = update
            super().add_update(update)
            self._var_objects[id(variable)] = variable

    # Run both branches in isolated scopes so variable assignments are
    # captured but not applied eagerly (same semantics as torch.cond).
    true_scope = _TrackingScope()
    with true_scope:
        true_val = true_fn()

    false_scope = _TrackingScope()
    with false_scope:
        false_val = false_fn()

    if isinstance(pred, bool):
        pred_ov = ov_opset.constant(pred, Type.boolean).output(0)
    else:
        pred_ov = get_ov_output(pred)
        if pred_ov.get_element_type() != Type.boolean:
            pred_ov = ov_opset.convert(pred_ov, Type.boolean).output(0)

    def _select(t, f):
        t_ov, f_ov = align_operand_types(
            get_ov_output(t), get_ov_output(f), "cond"
        )
        return OpenVINOKerasTensor(
            ov_opset.select(pred_ov, t_ov, f_ov).output(0)
        )

    # Apply selected variable updates: for each variable touched by either
    # branch, select between the true-branch value and the false-branch value
    # (defaulting to the pre-cond stored value for the branch that didn't
    # update it).
    all_var_ids = set(true_scope.state_mapping) | set(false_scope.state_mapping)
    for var_id in all_var_ids:
        if var_id in true_scope._var_objects:
            var = true_scope._var_objects[var_id]
        else:
            var = false_scope._var_objects[var_id]
        true_new = true_scope.state_mapping.get(var_id, var._value)
        false_new = false_scope.state_mapping.get(var_id, var._value)
        var._direct_assign(_select(true_new, false_new))

    if true_val is None:
        return None

    if isinstance(true_val, (list, tuple)):
        return type(true_val)(
            _select(t, f) for t, f in zip(true_val, false_val)
        )
    return _select(true_val, false_val)