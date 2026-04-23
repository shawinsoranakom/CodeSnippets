def export_openvino(self, prefix=colorstr("OpenVINO:")):
        """Export YOLO model to OpenVINO format."""
        from ultralytics.utils.export.openvino import torch2openvino

        # OpenVINO <= 2025.1.0 error on macOS 15.4+: https://github.com/openvinotoolkit/openvino/issues/30023
        check_requirements("openvino>=2025.2.0" if MACOS and MACOS_VERSION >= "15.4" else "openvino>=2024.0.0")
        import openvino as ov

        assert TORCH_2_1, f"OpenVINO export requires torch>=2.1 but torch=={TORCH_VERSION} is installed"

        def serialize(ov_model, file):
            """Set RT info, serialize, and save metadata YAML."""
            ov_model.set_rt_info("YOLO", ["model_info", "model_type"])
            ov_model.set_rt_info(True, ["model_info", "reverse_input_channels"])
            ov_model.set_rt_info(114, ["model_info", "pad_value"])
            ov_model.set_rt_info([255.0], ["model_info", "scale_values"])
            ov_model.set_rt_info(self.args.iou, ["model_info", "iou_threshold"])
            ov_model.set_rt_info([v.replace(" ", "_") for v in self.model.names.values()], ["model_info", "labels"])
            if self.model.task != "classify":
                ov_model.set_rt_info("fit_to_window_letterbox", ["model_info", "resize_type"])

            ov.save_model(ov_model, file, compress_to_fp16=self.args.half)
            YAML.save(Path(file).parent / "metadata.yaml", self.metadata)  # add metadata.yaml

        calibration_dataset, ignored_scope = None, None
        if self.args.int8:
            check_requirements("packaging>=23.2")  # must be installed first to build nncf wheel
            check_requirements("nncf>=2.14.0,<3.0.0" if not TORCH_2_3 else "nncf>=2.14.0")
            import nncf

            calibration_dataset = nncf.Dataset(self.get_int8_calibration_dataloader(prefix), self._transform_fn)
            if isinstance(self.model.model[-1], Detect):
                # Includes all Detect subclasses like Segment, Pose, OBB, WorldDetect, YOLOEDetect
                head_module_name = ".".join(list(self.model.named_modules())[-1][0].split(".")[:2])
                ignored_scope = nncf.IgnoredScope(  # ignore operations
                    patterns=[
                        f".*{head_module_name}/.*/Add",
                        f".*{head_module_name}/.*/Sub*",
                        f".*{head_module_name}/.*/Mul*",
                        f".*{head_module_name}/.*/Div*",
                    ],
                    types=["Sigmoid"],
                )

        ov_model = torch2openvino(
            model=NMSModel(self.model, self.args) if self.args.nms else self.model,
            im=self.im,
            dynamic=self.args.dynamic,
            half=self.args.half,
            int8=self.args.int8,
            calibration_dataset=calibration_dataset,
            ignored_scope=ignored_scope,
            prefix=prefix,
        )

        suffix = f"_{'int8_' if self.args.int8 else ''}openvino_model{os.sep}"
        f = str(self.file).replace(self.file.suffix, suffix)
        f_ov = str(Path(f) / self.file.with_suffix(".xml").name)

        serialize(ov_model, f_ov)
        return f