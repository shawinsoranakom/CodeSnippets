def _model_type(p: str = "path/to/model.pt", dnn: bool = False) -> str:
        """Take a path to a model file and return the model format string.

        Args:
            p (str): Path to the model file.
            dnn (bool): Whether to use OpenCV DNN module for ONNX inference.

        Returns:
            (str): Model format string (e.g., 'pt', 'onnx', 'engine', 'triton').

        Examples:
            >>> fmt = AutoBackend._model_type("path/to/model.onnx")
            >>> assert fmt == "onnx"
        """
        from ultralytics.engine.exporter import export_formats

        sf = export_formats()["Suffix"]
        if not is_url(p) and not isinstance(p, str):
            check_suffix(p, sf)
        name = Path(p).name
        types = [s in name for s in sf]
        types[5] |= name.endswith(".mlmodel")
        types[8] &= not types[9]
        format = next((f for i, f in enumerate(export_formats()["Argument"]) if types[i]), None)
        if format == "-":
            format = "pt"
        elif format == "onnx" and dnn:
            format = "dnn"
        elif not any(types):
            from urllib.parse import urlsplit

            url = urlsplit(p)
            if bool(url.netloc) and bool(url.path) and url.scheme in {"http", "grpc"}:
                format = "triton"
        return format