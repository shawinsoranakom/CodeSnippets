def update_device_map(self, device_map):
        if device_map is None:
            if torch.cuda.is_available():
                device_map = {"": torch.cuda.current_device()}
            elif is_torch_npu_available() and hasattr(torch, "npu"):
                device_map = {"": f"npu:{torch.npu.current_device()}"}
            elif is_torch_hpu_available() and hasattr(torch, "hpu"):
                device_map = {"": f"hpu:{torch.hpu.current_device()}"}
            elif is_torch_xpu_available():
                device_map = {"": torch.xpu.current_device()}
            else:
                device_map = {"": "cpu"}
            logger.info(
                "The device_map was not initialized. "
                f"Setting device_map to {device_map}. "
                "If you want to use the model for inference, please set device_map ='auto' "
            )
        return device_map