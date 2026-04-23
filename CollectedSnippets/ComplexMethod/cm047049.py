def model_kwargs(self, use_lora: bool, is_vision: bool) -> dict:
        """Return kwargs for trainer.prepare_model_for_training()."""
        # Determine target modules based on model type
        if use_lora and is_vision:
            # Vision models expect a string (e.g., "all-linear"); fall back to None to use trainer defaults
            target_modules = "all-linear" if self.lora.vision_all_linear else None
        else:
            parsed = [
                m.strip()
                for m in str(self.lora.target_modules).split(",")
                if m and m.strip()
            ]
            target_modules = parsed or None

        return {
            "use_lora": use_lora,
            "finetune_vision_layers": self.lora.finetune_vision_layers,
            "finetune_language_layers": self.lora.finetune_language_layers,
            "finetune_attention_modules": self.lora.finetune_attention_modules,
            "finetune_mlp_modules": self.lora.finetune_mlp_modules,
            "target_modules": target_modules,
            "lora_r": self.lora.lora_r,
            "lora_alpha": self.lora.lora_alpha,
            "lora_dropout": self.lora.lora_dropout,
            "use_gradient_checkpointing": self.training.gradient_checkpointing,
            "use_rslora": self.lora.use_rslora,
            "use_loftq": self.lora.use_loftq,
        }