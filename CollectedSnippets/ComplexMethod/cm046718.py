def _resolve_image(image_data):
        """Resolve image data to a PIL Image object."""
        if hasattr(image_data, "size") and hasattr(image_data, "mode"):
            return image_data  # Already PIL
        if isinstance(image_data, str):
            if image_data.startswith(("http://", "https://")):
                import fsspec
                from io import BytesIO

                with fsspec.open(image_data, "rb", expand = True) as f:
                    return Image.open(BytesIO(f.read())).convert("RGB")
            elif _image_lookup is not None and image_data in _image_lookup:
                from huggingface_hub import hf_hub_download

                local_path = hf_hub_download(
                    dataset_name,
                    _image_lookup[image_data],
                    repo_type = "dataset",
                )
                return Image.open(local_path).convert("RGB")
            else:
                return Image.open(image_data).convert("RGB")
        if isinstance(image_data, dict) and (
            "bytes" in image_data or "path" in image_data
        ):
            if image_data.get("bytes"):
                from io import BytesIO

                return Image.open(BytesIO(image_data["bytes"])).convert("RGB")
            if image_data.get("path"):
                return Image.open(image_data["path"]).convert("RGB")
        raise ValueError(f"Cannot resolve image: {type(image_data)}")