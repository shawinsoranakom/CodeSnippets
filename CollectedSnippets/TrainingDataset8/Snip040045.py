def add_file(index: int) -> None:
            file = UploadedFileRec(
                id=0, name=f"file_{index}", type="type", data=bytes(f"{index}", "utf-8")
            )
            added_files.append(self.mgr.add_file("session", f"widget_{index}", file))