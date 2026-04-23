def get_tolerance_and_cosine_flag(self, is_training, current_device, name):
        cosine = self.args.cosine
        if is_training:
            from torch._inductor import config as inductor_config

            if (name in self._config["tolerance"]["higher_training"]) or (
                inductor_config.max_autotune
                and name in self._config["tolerance"]["higher_max_autotune_training"]
            ):
                return 2e-2, cosine
            else:
                return 1e-2, cosine
        else:
            if (
                current_device == "cpu"
                and name in self._config["tolerance"]["higher_inference_cpu"]
            ):
                return 5e-3, cosine
            if name in self._config["tolerance"]["higher_inference"]:
                return 4e-3, cosine
        return 1e-3, cosine