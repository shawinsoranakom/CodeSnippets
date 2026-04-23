def load_model(self, weight: str | Path) -> None:
        """Load an ONNX model using ONNX Runtime or OpenCV DNN.

        Args:
            weight (str | Path): Path to the .onnx model file.
        """
        cuda = isinstance(self.device, torch.device) and torch.cuda.is_available() and self.device.type != "cpu"

        if self.format == "dnn":
            # OpenCV DNN
            LOGGER.info(f"Loading {weight} for ONNX OpenCV DNN inference...")
            check_requirements("opencv-python>=4.5.4")
            import cv2

            self.net = cv2.dnn.readNetFromONNX(weight)
        else:
            # ONNX Runtime
            LOGGER.info(f"Loading {weight} for ONNX Runtime inference...")
            check_requirements(("onnx", "onnxruntime-gpu" if cuda else "onnxruntime"))
            import onnxruntime

            # Select execution provider
            available = onnxruntime.get_available_providers()
            if cuda and "CUDAExecutionProvider" in available:
                providers = [("CUDAExecutionProvider", {"device_id": self.device.index}), "CPUExecutionProvider"]
            elif self.device.type == "mps" and "CoreMLExecutionProvider" in available:
                providers = ["CoreMLExecutionProvider", "CPUExecutionProvider"]
            else:
                providers = ["CPUExecutionProvider"]
                if cuda:
                    LOGGER.warning("CUDA requested but CUDAExecutionProvider not available. Using CPU...")
                    self.device = torch.device("cpu")
                    cuda = False

            LOGGER.info(
                f"Using ONNX Runtime {onnxruntime.__version__} with "
                f"{providers[0] if isinstance(providers[0], str) else providers[0][0]}"
            )

            self.session = onnxruntime.InferenceSession(weight, providers=providers)
            self.output_names = [x.name for x in self.session.get_outputs()]

            # Get metadata
            metadata_map = self.session.get_modelmeta().custom_metadata_map
            if metadata_map:
                self.apply_metadata(dict(metadata_map))

            # Check if dynamic shapes
            self.dynamic = isinstance(self.session.get_outputs()[0].shape[0], str)
            self.fp16 = "float16" in self.session.get_inputs()[0].type

            # Setup IO binding for CUDA
            self.use_io_binding = not self.dynamic and cuda
            if self.use_io_binding:
                self.io = self.session.io_binding()
                self.bindings = []
                for output in self.session.get_outputs():
                    out_fp16 = "float16" in output.type
                    y_tensor = torch.empty(output.shape, dtype=torch.float16 if out_fp16 else torch.float32).to(
                        self.device
                    )
                    self.io.bind_output(
                        name=output.name,
                        device_type=self.device.type,
                        device_id=self.device.index if cuda else 0,
                        element_type=np.float16 if out_fp16 else np.float32,
                        shape=tuple(y_tensor.shape),
                        buffer_ptr=y_tensor.data_ptr(),
                    )
                    self.bindings.append(y_tensor)