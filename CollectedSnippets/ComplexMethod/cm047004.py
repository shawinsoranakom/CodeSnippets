def _unsloth_trainer_init(self, *args, **kwargs):
            model = kwargs.get("model")
            if model is None and len(args) > 0:
                model = args[0]
            if model is not None:
                try:
                    apply_accepts_loss_kwargs_fix(model)
                except Exception:
                    pass
            _original_trainer_init(self, *args, **kwargs)
            try:
                accelerator = getattr(self, "accelerator", None)
                if (
                    accelerator is not None
                    and getattr(accelerator, "gradient_accumulation_steps", 1) > 1
                ):
                    accelerator.gradient_accumulation_steps = 1
                    gs = getattr(accelerator, "gradient_state", None)
                    if gs is not None and hasattr(gs, "plugin_kwargs"):
                        try:
                            gs.plugin_kwargs["num_steps"] = 1
                        except Exception:
                            pass
            except Exception:
                pass