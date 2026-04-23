def load_model(self, weight: str | torch.nn.Module) -> None:
        """Load a PyTorch model from a checkpoint file or nn.Module instance.

        Args:
            weight (str | torch.nn.Module): Path to the .pt checkpoint or a pre-loaded module.
        """
        from ultralytics.nn.tasks import load_checkpoint

        if isinstance(weight, torch.nn.Module):
            if self.fuse and hasattr(weight, "fuse"):
                if IS_JETSON and is_jetson(jetpack=5):
                    weight = weight.to(self.device)
                weight = weight.fuse(verbose=self.verbose)
            model = weight.to(self.device)
        else:
            model, _ = load_checkpoint(weight, device=self.device, fuse=self.fuse)

        # Extract model attributes
        if hasattr(model, "kpt_shape"):
            self.kpt_shape = model.kpt_shape
        self.stride = max(int(model.stride.max()), 32) if hasattr(model, "stride") else 32
        self.names = model.module.names if hasattr(model, "module") else getattr(model, "names", {})
        self.channels = model.yaml.get("channels", 3) if hasattr(model, "yaml") else 3
        model.half() if self.fp16 else model.float()

        for p in model.parameters():
            p.requires_grad = False

        self.model = model
        self.end2end = getattr(model, "end2end", False)