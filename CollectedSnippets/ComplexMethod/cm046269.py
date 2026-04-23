def configure(self) -> None:
        """Configure the model and load selected classes for inference."""
        # Add dropdown menu for model selection
        M_ORD, T_ORD = ["yolo26n", "yolo26s", "yolo26m", "yolo26l", "yolo26x"], ["", "-seg", "-pose", "-obb", "-cls"]
        available_models = sorted(
            [
                x.replace("yolo", "YOLO")
                for x in GITHUB_ASSETS_STEMS
                if any(x.startswith(b) for b in M_ORD) and "grayscale" not in x
            ],
            key=lambda x: (M_ORD.index(x[:7].lower()), T_ORD.index(x[7:].lower() or "")),
        )
        if self.model_path:  # Insert user provided custom model in available_models
            available_models.insert(0, self.model_path)
        selected_model = self.st.sidebar.selectbox("Model", available_models)

        with self.st.spinner("Model is downloading..."):
            if selected_model.endswith((".pt", ".onnx", ".torchscript", ".mlpackage", ".engine")) or any(
                fmt in selected_model for fmt in ("openvino_model", "rknn_model")
            ):
                model_path = selected_model
            else:
                model_path = f"{selected_model.lower()}.pt"  # Default to .pt if no model provided during function call.
            self.model = YOLO(model_path)  # Load the YOLO model
            class_names = list(self.model.names.values())  # Convert dictionary to list of class names
        self.st.success("Model loaded successfully!")

        # Multiselect box with class names and get indices of selected classes
        selected_classes = self.st.sidebar.multiselect("Classes", class_names, default=class_names[:3])
        self.selected_ind = [class_names.index(option) for option in selected_classes]

        if not isinstance(self.selected_ind, list):  # Ensure selected_options is a list
            self.selected_ind = list(self.selected_ind)