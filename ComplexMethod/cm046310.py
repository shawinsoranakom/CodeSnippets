def export_saved_model(self, prefix=colorstr("TensorFlow SavedModel:")):
        """Export YOLO model to TensorFlow SavedModel format."""
        cuda = torch.cuda.is_available()
        try:
            import tensorflow as tf
        except ImportError:
            check_requirements("tensorflow>=2.0.0,<=2.19.0")
            import tensorflow as tf
        check_requirements(
            (
                "tf_keras<=2.19.0",  # required by 'onnx2tf' package
                "sng4onnx>=1.0.1",  # required by 'onnx2tf' package
                "onnx_graphsurgeon>=0.3.26",  # required by 'onnx2tf' package
                "ai-edge-litert>=1.2.0" + (",<1.4.0" if MACOS else ""),  # required by 'onnx2tf' package
                "onnx>=1.12.0,<2.0.0",
                "onnx2tf>=1.26.3,<1.29.0",  # pin to avoid h5py build issues on aarch64
                "onnxslim>=0.1.71",
                "onnxruntime-gpu" if cuda else "onnxruntime",
                "protobuf>=5",
            ),
            cmds="--extra-index-url https://pypi.ngc.nvidia.com",  # onnx_graphsurgeon only on NVIDIA
        )

        LOGGER.info(f"\n{prefix} starting export with tensorflow {tf.__version__}...")
        check_version(
            tf.__version__,
            ">=2.0.0",
            name="tensorflow",
            verbose=True,
            msg="https://github.com/ultralytics/ultralytics/issues/5161",
        )
        from ultralytics.utils.export.tensorflow import onnx2saved_model

        f = Path(str(self.file).replace(self.file.suffix, "_saved_model"))
        if f.is_dir():
            shutil.rmtree(f)  # delete output folder

        # Export to TF
        images = None
        if self.args.int8 and self.args.data:
            images = [batch["img"] for batch in self.get_int8_calibration_dataloader(prefix)]
            images = (
                torch.nn.functional.interpolate(torch.cat(images, 0).float(), size=self.imgsz)
                .permute(0, 2, 3, 1)
                .numpy()
                .astype(np.float32)
            )

        # Export to ONNX
        if isinstance(self.model.model[-1], RTDETRDecoder):
            self.args.opset = self.args.opset or 19
            assert 16 <= self.args.opset <= 19, "RTDETR export requires opset>=16;<=19"
        self.args.simplify = True
        f_onnx = self.export_onnx()  # ensure ONNX is available
        keras_model = onnx2saved_model(
            f_onnx,
            f,
            int8=self.args.int8,
            images=images,
            disable_group_convolution=self.args.format in {"tfjs", "edgetpu"},
            prefix=prefix,
        )
        YAML.save(f / "metadata.yaml", self.metadata)  # add metadata.yaml
        # Add TFLite metadata
        for file in f.rglob("*.tflite"):
            file.unlink() if "quant_with_int16_act.tflite" in str(file) else self._add_tflite_metadata(file)

        return str(f), keras_model