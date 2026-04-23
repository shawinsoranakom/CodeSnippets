async def _filter(self, filenames: Optional[List[Union[str, Path]]] = None) -> (List[Path], List[Path]):
        """Filter the provided filenames to only include valid text files.

        Args:
            filenames (Optional[List[Union[str, Path]]]): List of filenames to filter.

        Returns:
            Tuple[List[Path], List[Path]]: A tuple containing a list of valid pathnames and a list of excluded paths.
        """
        root_path = Path(self.root_path).absolute()
        if not filenames:
            filenames = [root_path]
        pathnames = []
        excludes = []
        for i in filenames:
            path = Path(i).absolute()
            if not path.is_relative_to(root_path):
                excludes.append(path)
                logger.debug(f"{path} not is_relative_to {root_path})")
                continue
            if not path.is_dir():
                is_text = await File.is_textual_file(path)
                if is_text:
                    pathnames.append(path)
                continue
            subfiles = list_files(path)
            for j in subfiles:
                is_text = await File.is_textual_file(j)
                if is_text:
                    pathnames.append(j)

        logger.debug(f"{pathnames}, excludes:{excludes})")
        return pathnames, excludes