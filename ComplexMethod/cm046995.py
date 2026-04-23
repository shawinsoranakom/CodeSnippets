def _shadow_accepts_loss_kwargs(model, value):
    # Set the attribute at every wrapper level so HF's hasattr check resolves
    # regardless of where accelerator / peft unwrap lands.
    seen = set()
    m = model
    for _ in range(8):
        if m is None or id(m) in seen:
            break
        seen.add(id(m))
        try:
            setattr(m, "accepts_loss_kwargs", value)
        except Exception:
            pass
        nxt = getattr(m, "base_model", None)
        if nxt is None or nxt is m:
            nxt = getattr(m, "model", None)
        if nxt is None or nxt is m:
            break
        m = nxt