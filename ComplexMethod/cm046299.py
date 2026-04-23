def forward(self, x: list[torch.Tensor]) -> tuple | list[torch.Tensor] | dict[str, torch.Tensor]:
        """Return model outputs and mask coefficients if training, otherwise return outputs and mask coefficients."""
        outputs = Detect.forward(self, x)
        preds = outputs[1] if isinstance(outputs, tuple) else outputs
        proto = self.proto(x)  # mask protos
        if isinstance(preds, dict):  # training and validating during training
            if self.end2end:
                preds["one2many"]["proto"] = proto
                preds["one2one"]["proto"] = (
                    tuple(p.detach() for p in proto) if isinstance(proto, tuple) else proto.detach()
                )
            else:
                preds["proto"] = proto
        if self.training:
            return preds
        return (outputs, proto) if self.export else ((outputs[0], proto), preds)