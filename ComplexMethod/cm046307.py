def export_onnx(self, prefix=colorstr("ONNX:")):
        """Export YOLO model to ONNX format."""
        requirements = ["onnx>=1.12.0,<2.0.0"]
        if self.args.simplify:
            requirements += ["onnxslim>=0.1.71", "onnxruntime" + ("-gpu" if torch.cuda.is_available() else "")]
        check_requirements(requirements)
        import onnx

        from ultralytics.utils.export.engine import best_onnx_opset, torch2onnx

        opset = self.args.opset or best_onnx_opset(onnx, cuda="cuda" in self.device.type)
        LOGGER.info(f"\n{prefix} starting export with onnx {onnx.__version__} opset {opset}...")
        if self.args.nms:
            assert TORCH_1_13, f"'nms=True' ONNX export requires torch>=1.13 (found torch=={TORCH_VERSION})"

        f = str(self.file.with_suffix(".onnx"))
        output_names = ["output0", "output1"] if self.model.task == "segment" else ["output0"]
        dynamic = self.args.dynamic
        if dynamic:
            dynamic = {"images": {0: "batch", 2: "height", 3: "width"}}  # shape(1,3,640,640)
            if isinstance(self.model, SegmentationModel):
                dynamic["output0"] = {0: "batch", 2: "anchors"}  # shape(1, 116, 8400)
                dynamic["output1"] = {0: "batch", 2: "mask_height", 3: "mask_width"}  # shape(1,32,160,160)
            elif isinstance(self.model, DetectionModel):
                dynamic["output0"] = {0: "batch", 2: "anchors"}  # shape(1, 84, 8400)
            if self.args.nms:  # only batch size is dynamic with NMS
                dynamic["output0"].pop(2)
        if self.args.nms and self.model.task == "obb":
            self.args.opset = opset  # for NMSModel
            self.args.simplify = True  # fix OBB runtime error related to topk

        with arange_patch(dynamic=bool(dynamic), half=self.args.half, fmt=self.args.format):
            torch2onnx(
                NMSModel(self.model, self.args) if self.args.nms else self.model,
                self.im,
                f,
                opset=opset,
                input_names=["images"],
                output_names=output_names,
                dynamic=dynamic or None,
            )

        # Checks
        model_onnx = onnx.load(f)  # load onnx model

        # Simplify
        if self.args.simplify:
            try:
                import onnxslim

                LOGGER.info(f"{prefix} slimming with onnxslim {onnxslim.__version__}...")
                model_onnx = onnxslim.slim(model_onnx)

            except Exception as e:
                LOGGER.warning(f"{prefix} simplifier failure: {e}")

        # Metadata
        for k, v in self.metadata.items():
            meta = model_onnx.metadata_props.add()
            meta.key, meta.value = k, str(v)

        # IR version
        if getattr(model_onnx, "ir_version", 0) > 10:
            LOGGER.info(f"{prefix} limiting IR version {model_onnx.ir_version} to 10 for ONNXRuntime compatibility...")
            model_onnx.ir_version = 10

        # FP16 conversion for CPU export (GPU exports are already FP16 from model.half() during tracing)
        if self.args.half and self.args.format == "onnx" and self.device.type == "cpu":
            try:
                from onnxruntime.transformers import float16

                LOGGER.info(f"{prefix} converting to FP16...")
                model_onnx = float16.convert_float_to_float16(model_onnx, keep_io_types=True)
            except Exception as e:
                LOGGER.warning(f"{prefix} FP16 conversion failure: {e}")

        onnx.save(model_onnx, f)
        return f