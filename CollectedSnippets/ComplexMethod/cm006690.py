def model_post_init(self, /, _context: Any) -> None:
        new_files: list[Any] = []
        for file in self.files or []:
            # Skip if already an Image instance
            if isinstance(file, Image):
                new_files.append(file)
            # Get the path string if file is a dict or has path attribute
            elif isinstance(file, dict) and "path" in file:
                file_path = file["path"]
                if file_path and is_image_file(file_path):
                    new_files.append(Image(path=file_path))
                else:
                    new_files.append(file_path if file_path else file)
            elif hasattr(file, "path") and file.path:
                if is_image_file(file.path):
                    new_files.append(Image(path=file.path))
                else:
                    new_files.append(file.path)
            elif isinstance(file, str) and is_image_file(file):
                new_files.append(Image(path=file))
            else:
                new_files.append(file)
        self.files = new_files
        if "timestamp" not in self.data:
            self.data["timestamp"] = self.timestamp