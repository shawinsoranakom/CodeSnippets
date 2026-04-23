def export_coreml(self, prefix=colorstr("CoreML:")):
        """Export YOLO model to CoreML format."""
        mlmodel = self.args.format.lower() == "mlmodel"  # legacy *.mlmodel export format requested
        from ultralytics.utils.export.coreml import IOSDetectModel, pipeline_coreml, torch2coreml

        # latest numpy 2.4.0rc1 breaks coremltools exports
        check_requirements(["coremltools>=9.0", "numpy>=1.14.5,<=2.3.5"])
        import coremltools as ct

        assert not WINDOWS, "CoreML export is not supported on Windows, please run on macOS or Linux."
        assert TORCH_1_11, "CoreML export requires torch>=1.11"
        if self.args.batch > 1:
            assert self.args.dynamic, (
                "batch sizes > 1 are not supported without 'dynamic=True' for CoreML export. Please retry at 'dynamic=True'."
            )
        if self.args.dynamic:
            assert not self.args.nms, (
                "'nms=True' cannot be used together with 'dynamic=True' for CoreML export. Please disable one of them."
            )
            assert self.model.task != "classify", "'dynamic=True' is not supported for CoreML classification models."
        f = self.file.with_suffix(".mlmodel" if mlmodel else ".mlpackage")
        if f.is_dir():
            shutil.rmtree(f)

        if self.model.task == "detect":
            model = IOSDetectModel(self.model, self.im, mlprogram=not mlmodel) if self.args.nms else self.model
        else:
            if self.args.nms:
                LOGGER.warning(f"{prefix} 'nms=True' is only available for Detect models like 'yolo26n.pt'.")
                # TODO CoreML Segment and Pose model pipelining
            model = self.model

        if self.args.dynamic:
            input_shape = ct.Shape(
                shape=(
                    ct.RangeDim(lower_bound=1, upper_bound=self.args.batch, default=1),
                    self.im.shape[1],
                    ct.RangeDim(lower_bound=32, upper_bound=self.imgsz[0] * 2, default=self.imgsz[0]),
                    ct.RangeDim(lower_bound=32, upper_bound=self.imgsz[1] * 2, default=self.imgsz[1]),
                )
            )
            inputs = [ct.TensorType("image", shape=input_shape)]
        else:
            inputs = [ct.ImageType("image", shape=self.im.shape, scale=1 / 255, bias=[0.0, 0.0, 0.0])]

        ct_model = torch2coreml(
            model=model,
            inputs=inputs,
            im=self.im,
            classifier_names=list(self.model.names.values()) if self.model.task == "classify" else None,
            mlmodel=mlmodel,
            half=self.args.half,
            int8=self.args.int8,
            metadata=self.metadata,
            prefix=prefix,
        )

        if self.args.nms and self.model.task == "detect":
            ct_model = pipeline_coreml(
                ct_model,
                self.output_shape,
                weights_dir=None if mlmodel else ct_model.weights_dir,
                metadata=self.metadata,
                mlmodel=mlmodel,
                iou=self.args.iou,
                conf=self.args.conf,
                agnostic_nms=self.args.agnostic_nms,
                prefix=prefix,
            )

        if self.model.task == "classify":
            ct_model.user_defined_metadata.update({"com.apple.coreml.model.preview.type": "imageClassifier"})

        try:
            ct_model.save(str(f))  # save *.mlpackage
        except Exception as e:
            LOGGER.warning(
                f"{prefix} CoreML export to *.mlpackage failed ({e}), reverting to *.mlmodel export. "
                f"Known coremltools Python 3.11 and Windows bugs https://github.com/apple/coremltools/issues/1928."
            )
            f = f.with_suffix(".mlmodel")
            ct_model.save(str(f))
        return f