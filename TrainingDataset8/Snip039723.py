def add_file(ii: int) -> None:
            coord = random_coordinates()
            data = bytes(f"{ii}", "utf-8")
            self.media_file_manager.add(data, "image/png", coord)