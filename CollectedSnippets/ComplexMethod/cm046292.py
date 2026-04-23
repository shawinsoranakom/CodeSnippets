def load_model(self, weight: str | Path) -> None:
        """Load an Intel OpenVINO IR model from a .xml/.bin file pair or model directory.

        Args:
            weight (str | Path): Path to the .xml file or directory containing OpenVINO model files.
        """
        LOGGER.info(f"Loading {weight} for OpenVINO inference...")
        check_requirements("openvino>=2024.0.0")
        import openvino as ov

        core = ov.Core()
        fallback_device = "CPU" if core.available_devices == ["CPU"] else "AUTO"
        device_name = fallback_device

        if isinstance(self.device, str) and self.device.startswith("intel"):
            device_name = self.device.split(":")[1].upper()
            self.device = torch.device("cpu")
            if device_name not in core.available_devices:
                LOGGER.warning(f"OpenVINO device '{device_name}' not available. Using '{fallback_device}' instead.")
                device_name = fallback_device

        w = Path(weight)
        if not w.is_file():
            w = next(w.glob("*.xml"))

        ov_model = core.read_model(model=str(w), weights=w.with_suffix(".bin"))
        if ov_model.get_parameters()[0].get_layout().empty:
            ov_model.get_parameters()[0].set_layout(ov.Layout("NCHW"))

        # Load metadata
        metadata_file = w.parent / "metadata.yaml"
        if metadata_file.exists():
            from ultralytics.utils import YAML

            self.apply_metadata(YAML.load(metadata_file))

        # Set inference mode
        self.inference_mode = "CUMULATIVE_THROUGHPUT" if self.dynamic and self.batch > 1 else "LATENCY"
        config = {"PERFORMANCE_HINT": self.inference_mode}
        if LINUX and ARM64 and device_name == "CPU":
            config["EXECUTION_MODE_HINT"] = ov.properties.hint.ExecutionMode.ACCURACY
            config["INFERENCE_PRECISION_HINT"] = ov.Type.f32

        self.ov_compiled_model = core.compile_model(
            ov_model,
            device_name=device_name,
            config=config,
        )
        LOGGER.info(
            f"Using OpenVINO {self.inference_mode} mode for batch={self.batch} inference on "
            f"{', '.join(self.ov_compiled_model.get_property('EXECUTION_DEVICES'))}..."
        )
        self.input_name = self.ov_compiled_model.input().get_any_name()
        self.ov = ov