def _patched_init(self, *args, **kwargs):
        # Extract model and training_args
        model = kwargs.get("model") or (args[0] if args else None)
        training_args = kwargs.get("args") or (args[1] if len(args) > 1 else None)

        # Check if model has pending compile
        if (
            model is not None
            and training_args is not None
            and getattr(model, "_compile_pending", False)
        ):
            max_steps = getattr(training_args, "max_steps", -1)
            compile_mode = getattr(model, "_compile_mode", "default")

            # Re-estimate threshold now that training args are available
            batch_size = getattr(training_args, "per_device_train_batch_size", None)
            grad_accum = getattr(training_args, "gradient_accumulation_steps", None)
            max_seq_length = getattr(model, "max_seq_length", None)
            if max_seq_length is None and hasattr(model, "__getitem__"):
                try:
                    max_seq_length = getattr(model[0], "max_seq_length", None)
                except Exception:
                    max_seq_length = None
            if max_seq_length is None:
                tokenizer = getattr(model, "tokenizer", None)
                max_seq_length = (
                    getattr(tokenizer, "model_max_length", None)
                    if tokenizer is not None
                    else None
                )

            threshold = FastSentenceTransformer._estimate_compile_threshold(
                model,
                batch_size = batch_size,
                grad_accum = grad_accum,
                max_seq_length = max_seq_length,
            )
            model._compile_threshold = threshold

            if max_steps > 0 and max_steps >= threshold:
                print(
                    f"Unsloth: Auto-compiling model ({max_steps} steps >= {threshold} threshold)"
                )
                FastSentenceTransformer._apply_torch_compile(model, mode = compile_mode)
                model._compile_pending = False
            elif max_steps > 0:
                print(
                    f"Unsloth: Skipping torch.compile ({max_steps} steps < {threshold} threshold)"
                )
                model._compile_pending = False

        # Call original __init__
        _original_init(self, *args, **kwargs)

        # Disable mixed precision when FORCE_FLOAT32 is active (matches rl.py behavior)
        if os.environ.get("UNSLOTH_FORCE_FLOAT32", "0") == "1":
            if hasattr(self, "args") and self.args is not None:
                if self.args.fp16 or self.args.bf16:
                    print(
                        "Unsloth: Switching to float32 training since model cannot work with float16"
                    )
                    self.args.fp16 = False
                    self.args.bf16 = False
                    if hasattr(self.args, "bf16_full_eval"):
                        self.args.bf16_full_eval = False
                    if hasattr(self.args, "fp16_full_eval"):
                        self.args.fp16_full_eval = False