def quantize(self, model):
        # Helper function that quantizes the given model
        # Recursively convert all the `quant_mode` attributes as `True`
        if hasattr(model, "quant_mode"):
            model.quant_mode = True
        elif isinstance(model, nn.Sequential):
            for n, m in model.named_children():
                self.quantize(m)
        elif isinstance(model, nn.ModuleList):
            for n in model:
                self.quantize(n)
        else:
            for attr in dir(model):
                mod = getattr(model, attr)
                if isinstance(mod, nn.Module) and mod != model:
                    self.quantize(mod)