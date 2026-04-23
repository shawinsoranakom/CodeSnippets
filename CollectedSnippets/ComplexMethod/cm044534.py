def _filetypes(self) -> dict[str, list[tuple[str, str]]]:
        """ dict: The accepted extensions for each file type for opening/saving """
        all_files = ("All files", "*.*")
        filetypes = {
            "default": [all_files],
            "alignments": [("Faceswap Alignments", "*.fsa"), all_files],
            "config_project": [("Faceswap Project files", "*.fsw"), all_files],
            "config_task": [("Faceswap Task files", "*.fst"), all_files],
            "config_all": [("Faceswap Project and Task files", "*.fst *.fsw"), all_files],
            "csv": [("Comma separated values", "*.csv"), all_files],
            "image": [("Bitmap", "*.bmp"),
                      ("JPG", "*.jpeg *.jpg"),
                      ("PNG", "*.png"),
                      ("TIFF", "*.tif *.tiff"),
                      all_files],
            "ini": [("Faceswap config files", "*.ini"), all_files],
            "json": [("JSON file", "*.json"), all_files],
            "model": [("Keras model files", "*.keras"), all_files],
            "state": [("State files", "*.json"), all_files],
            "log": [("Log files", "*.log"), all_files],
            "video": [("Audio Video Interleave", "*.avi"),
                      ("Flash Video", "*.flv"),
                      ("Matroska", "*.mkv"),
                      ("MOV", "*.mov"),
                      ("MP4", "*.mp4"),
                      ("MPEG", "*.mpeg *.mpg *.ts *.vob"),
                      ("WebM", "*.webm"),
                      ("Windows Media Video", "*.wmv"),
                      all_files]}

        # Add in multi-select options and upper case extensions for Linux
        for key in filetypes:
            if platform.system() == "Linux":
                filetypes[key] = [item
                                  if item[0] == "All files"
                                  else (item[0], f"{item[1]} {item[1].upper()}")
                                  for item in filetypes[key]]
            if len(filetypes[key]) > 2:
                multi = [f"{key.title()} Files"]
                multi.append(" ".join([ftype[1]
                                       for ftype in filetypes[key] if ftype[0] != "All files"]))
                filetypes[key].insert(0, T.cast(tuple[str, str], tuple(multi)))
        return filetypes