def __init__(
        self,
        model: str | torch.nn.Module = "yolo26n.pt",
        device: torch.device = torch.device("cpu"),
        dnn: bool = False,
        data: str | Path | None = None,
        fp16: bool = False,
        fuse: bool = True,
        verbose: bool = True,
    ):
        """Initialize the AutoBackend for inference.

        Args:
            model (str | torch.nn.Module): Path to the model weights file or a module instance.
            device (torch.device): Device to run the model on.
            dnn (bool): Use OpenCV DNN module for ONNX inference.
            data (str | Path, optional): Path to the additional data.yaml file containing class names.
            fp16 (bool): Enable half-precision inference. Supported only on specific backends.
            fuse (bool): Fuse Conv2D + BatchNorm layers for optimization.
            verbose (bool): Enable verbose logging.
        """
        super().__init__()
        # Determine model format from path/URL
        format = "pt" if isinstance(model, nn.Module) else self._model_type(model, dnn)

        # Check if format supports FP16
        fp16 &= format in {"pt", "torchscript", "onnx", "openvino", "engine", "triton"}

        # Set device
        if (
            isinstance(device, torch.device)
            and torch.cuda.is_available()
            and device.type != "cpu"
            and format not in {"pt", "torchscript", "engine", "onnx", "paddle"}
        ):
            device = torch.device("cpu")

        # Select and initialize the appropriate backend
        backend_kwargs = {"device": device, "fp16": fp16}

        if format == "tfjs":
            raise NotImplementedError("Ultralytics TF.js inference is not currently supported.")
        if format not in self._BACKEND_MAP:
            from ultralytics.engine.exporter import export_formats

            raise TypeError(
                f"model='{model}' is not a supported model format. "
                f"Ultralytics supports: {export_formats()['Format']}\n"
                f"See https://docs.ultralytics.com/modes/predict for help."
            )
        if format == "pt":
            backend_kwargs["fuse"] = fuse
            backend_kwargs["verbose"] = verbose
        elif format in {"saved_model", "pb", "tflite", "edgetpu", "dnn"}:
            backend_kwargs["format"] = format
        self.backend = self._BACKEND_MAP[format](model, **backend_kwargs)

        self.nhwc = format in {"coreml", "saved_model", "pb", "tflite", "edgetpu", "rknn"}
        self.format = format

        # Ensure backend has names (fallback to default if not set by metadata)
        if not self.backend.names:
            self.backend.names = default_class_names(data)
        self.backend.names = check_class_names(self.backend.names)