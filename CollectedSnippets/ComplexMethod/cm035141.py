def _process_input_for_service(
        self, input_data: str, file_type: Optional[str]
    ) -> tuple[str, Optional[str]]:
        if _is_url(input_data):
            norm_ft = None
            if isinstance(file_type, str):
                if file_type.lower() in ("None", "none", "null", "unknown", ""):
                    norm_ft = None
                else:
                    norm_ft = file_type.lower()
            return input_data, norm_ft
        elif _is_base64(input_data):
            try:
                if input_data.startswith("data:"):
                    base64_data = input_data.split(",", 1)[1]
                else:
                    base64_data = input_data
                bytes_ = base64.b64decode(base64_data)
                file_type_str = _infer_file_type_from_bytes(bytes_)
                if file_type_str is None:
                    raise ValueError(
                        "Unsupported file type in Base64 data. "
                        "Only images (JPEG, PNG, etc.) and PDF documents are supported."
                    )
                return input_data, file_type_str
            except Exception as e:
                raise ValueError(f"Failed to decode Base64 data: {str(e)}") from e
        elif _is_file_path(input_data):
            try:
                with open(input_data, "rb") as f:
                    bytes_ = f.read()
                input_data = base64.b64encode(bytes_).decode("ascii")
                file_type_str = _infer_file_type_from_bytes(bytes_)
                if file_type_str is None:
                    raise ValueError(
                        f"Unsupported file type for '{input_data}'. "
                        "Only images (JPEG, PNG, etc.) and PDF documents are supported."
                    )
                return input_data, file_type_str
            except Exception as e:
                raise ValueError(f"Failed to read file: {str(e)}") from e
        else:
            raise ValueError("Invalid input data format")