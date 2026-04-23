def enable_half_precision(self, enable: bool = True, save: bool = True):
        """
        To enable half precision for the TTS model.
        Args:
            enable: bool, whether to enable half precision.

        """
        if str(self.configs.device) == "cpu" and enable:
            print("Half precision is not supported on CPU.")
            return

        self.configs.is_half = enable
        self.precision = torch.float16 if enable else torch.float32
        if save:
            self.configs.save_configs()
        if enable:
            if self.t2s_model is not None:
                self.t2s_model = self.t2s_model.half()
            if self.vits_model is not None:
                self.vits_model = self.vits_model.half()
            if self.bert_model is not None:
                self.bert_model = self.bert_model.half()
            if self.cnhuhbert_model is not None:
                self.cnhuhbert_model = self.cnhuhbert_model.half()
            if self.vocoder is not None:
                self.vocoder = self.vocoder.half()
        else:
            if self.t2s_model is not None:
                self.t2s_model = self.t2s_model.float()
            if self.vits_model is not None:
                self.vits_model = self.vits_model.float()
            if self.bert_model is not None:
                self.bert_model = self.bert_model.float()
            if self.cnhuhbert_model is not None:
                self.cnhuhbert_model = self.cnhuhbert_model.float()
            if self.vocoder is not None:
                self.vocoder = self.vocoder.float()