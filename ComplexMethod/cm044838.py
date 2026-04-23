def set_device(self, device: torch.device, save: bool = True):
        """
        To set the device for all models.
        Args:
            device: torch.device, the device to use for all models.
        """
        self.configs.device = device
        if save:
            self.configs.save_configs()
        if self.t2s_model is not None:
            self.t2s_model = self.t2s_model.to(device)
        if self.vits_model is not None:
            self.vits_model = self.vits_model.to(device)
        if self.bert_model is not None:
            self.bert_model = self.bert_model.to(device)
        if self.cnhuhbert_model is not None:
            self.cnhuhbert_model = self.cnhuhbert_model.to(device)
        if self.vocoder is not None:
            self.vocoder = self.vocoder.to(device)
        if self.sr_model is not None:
            self.sr_model = self.sr_model.to(device)