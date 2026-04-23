def patch_trl_disable_gradient_checkpointing():
    # TRL 1.0.0+ wraps generation in:
    #   with torch.no_grad(), disable_gradient_checkpointing(self.model, ...):
    # The toggle exists only to suppress a cosmetic PyTorch warning
    # ("None of the inputs have requires_grad=True"). Inside torch.no_grad()
    # the gradient checkpointing state has no functional effect on the
    # forward pass.
    #
    # On exit, the context manager calls model.gradient_checkpointing_enable()
    # which dispatches to HuggingFace's generic implementation and overwrites
    # Unsloth's custom `use_gradient_checkpointing="unsloth"` wrapper. For
    # Gemma-4 (and likely other models) this corrupts the forward numerics
    # enough to make GRPO KL divergence explode to ~10^12 at step 1.
    #
    # Replacing the context manager with a no-op preserves Unsloth's custom
    # gradient checkpointing wrapper across generation/inference passes.
    #
    # Backwards compatibility:
    #   - trl < 1.0.0 (no disable_gradient_checkpointing): early return.
    #   - trl >= 1.0.0: noop is functionally equivalent for forward
    #     correctness. The only loss is a cosmetic warning being emitted
    #     by PyTorch when use_reentrant=True (which is exactly the warning
    #     TRL added the toggle to suppress in the first place).
    try:
        import trl.models.utils as _tmu
    except ImportError:
        return
    if not hasattr(_tmu, "disable_gradient_checkpointing"):
        return
    if getattr(
        _tmu.disable_gradient_checkpointing,
        "_unsloth_noop_patched",
        False,
    ):
        return

    @contextmanager
    def _noop_disable_gradient_checkpointing(model, gradient_checkpointing_kwargs = None):
        yield

    _noop_disable_gradient_checkpointing._unsloth_noop_patched = True

    _tmu.disable_gradient_checkpointing = _noop_disable_gradient_checkpointing

    # Also rebind any trl.* module that already imported the symbol by
    # reference, so the noop applies even when the trainer module cached the
    # original at import time. We walk sys.modules dynamically rather than
    # hardcoding a list, so this picks up every trainer that does
    # `from ...models.utils import disable_gradient_checkpointing`
    # (grpo, dpo, rloo, dppo, gfpo, grpo_with_replay_buffer, and any future
    # TRL trainer module).
    for _mod_name, _mod in list(sys.modules.items()):
        if _mod is None or not _mod_name.startswith("trl."):
            continue
        try:
            _bound = getattr(_mod, "disable_gradient_checkpointing", None)
        except (AttributeError, ImportError):
            continue
        if _bound is None:
            continue
        try:
            setattr(
                _mod,
                "disable_gradient_checkpointing",
                _noop_disable_gradient_checkpointing,
            )
        except (AttributeError, TypeError):
            pass

    if os.environ.get("UNSLOTH_ENABLE_LOGGING", "0") == "1":
        logger.warning_once(
            "Unsloth: Patched trl.models.utils.disable_gradient_checkpointing with "
            "a no-op to preserve Unsloth gradient checkpointing across TRL "
            "generation passes."
        )
    return