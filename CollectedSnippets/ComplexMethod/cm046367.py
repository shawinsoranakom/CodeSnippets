def run(self):
        """Profile YOLO models for speed and accuracy across various formats including ONNX and TensorRT.

        Returns:
            (list[dict]): List of dictionaries containing profiling results for each model.

        Examples:
            Profile models and print results
            >>> from ultralytics.utils.benchmarks import ProfileModels
            >>> profiler = ProfileModels(["yolo26n.yaml", "yolo11s.yaml"])
            >>> results = profiler.run()
        """
        files = self.get_files()

        if not files:
            LOGGER.warning("No matching *.pt or *.onnx files found.")
            return []

        table_rows = []
        output = []
        for file in files:
            engine_file = file.with_suffix(".engine")
            if file.suffix in {".pt", ".yaml", ".yml"}:
                model = YOLO(str(file))
                model.fuse()  # to report correct params and GFLOPs in model.info()
                model_info = model.info(imgsz=self.imgsz)
                if self.trt and self.device.type != "cpu" and not engine_file.is_file():
                    engine_file = model.export(
                        format="engine",
                        half=self.half,
                        imgsz=self.imgsz,
                        device=self.device,
                        verbose=False,
                    )
                onnx_file = model.export(
                    format="onnx",
                    imgsz=self.imgsz,
                    device=self.device,
                    verbose=False,
                )
            elif file.suffix == ".onnx":
                model_info = self.get_onnx_model_info(file)
                onnx_file = file
            else:
                continue

            t_engine = self.profile_tensorrt_model(str(engine_file))
            t_onnx = self.profile_onnx_model(str(onnx_file))
            table_rows.append(self.generate_table_row(file.stem, t_onnx, t_engine, model_info))
            output.append(self.generate_results_dict(file.stem, t_onnx, t_engine, model_info))

        self.print_table(table_rows)
        return output