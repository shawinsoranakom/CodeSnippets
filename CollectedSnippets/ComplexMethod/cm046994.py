def _find_concrete_accepts_loss_kwargs(model):
    # Walk wrapper chain for first class that declares accepts_loss_kwargs in its
    # own __mro__ dict. Avoids PEFT __getattr__ forwarding and our own shadow.
    seen = set()
    m = model
    for _ in range(6):
        if m is None or id(m) in seen:
            break
        seen.add(id(m))
        for klass in type(m).__mro__:
            if "accepts_loss_kwargs" in klass.__dict__:
                return klass.__dict__[
                    "accepts_loss_kwargs"
                ], f"{klass.__name__}.accepts_loss_kwargs"
        nxt = getattr(m, "base_model", None)
        if nxt is None or nxt is m:
            nxt = getattr(m, "model", None)
        if nxt is None or nxt is m:
            break
        m = nxt
    return None, "no explicit accepts_loss_kwargs on any wrapper level"