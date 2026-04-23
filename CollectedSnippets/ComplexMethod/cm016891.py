def get_model_previews(self, filepath: str) -> list[str | BytesIO]:
        dirname = os.path.dirname(filepath)

        if not os.path.exists(dirname):
            return []

        basename = os.path.splitext(filepath)[0]
        match_files = glob.glob(f"{basename}.*", recursive=False)
        image_files = filter_files_content_types(match_files, "image")
        safetensors_file = next(filter(lambda x: x.endswith(".safetensors"), match_files), None)
        safetensors_metadata = {}

        result: list[str | BytesIO] = []

        for filename in image_files:
            _basename = os.path.splitext(filename)[0]
            if _basename == basename:
                result.append(filename)
            if _basename == f"{basename}.preview":
                result.append(filename)

        if safetensors_file:
            safetensors_filepath = os.path.join(dirname, safetensors_file)
            header = comfy.utils.safetensors_header(safetensors_filepath, max_size=8*1024*1024)
            if header:
                safetensors_metadata = json.loads(header)
        safetensors_images = safetensors_metadata.get("__metadata__", {}).get("ssmd_cover_images", None)
        if safetensors_images:
            safetensors_images = json.loads(safetensors_images)
            for image in safetensors_images:
                result.append(BytesIO(base64.b64decode(image)))

        return result