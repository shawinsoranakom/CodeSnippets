def reload(self):
        """
        Clears the style database and reloads the styles from the CSV file(s)
        matching the path used to initialize the database.
        """
        self.styles.clear()

        # scans for all styles files
        all_styles_files = []
        for pattern in self.paths:
            folder, file = os.path.split(pattern)
            if '*' in file or '?' in file:
                found_files = Path(folder).glob(file)
                [all_styles_files.append(file) for file in found_files]
            else:
                # if os.path.exists(pattern):
                all_styles_files.append(Path(pattern))

        # Remove any duplicate entries
        seen = set()
        self.all_styles_files = [s for s in all_styles_files if not (s in seen or seen.add(s))]

        for styles_file in self.all_styles_files:
            if len(all_styles_files) > 1:
                # add divider when more than styles file
                # '---------------- STYLES ----------------'
                divider = f' {styles_file.stem.upper()} '.center(40, '-')
                self.styles[divider] = PromptStyle(f"{divider}", None, None, "do_not_save")
            if styles_file.is_file():
                self.load_from_csv(styles_file)