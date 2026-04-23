def analyze_directory(
        self,
        directory: Path,
        identifier: str | None = None,
        ignore_files: list[str] | None = None,
        n_identifier: str | list[str] | None = None,
        only_modules: bool = True,
    ):
        """
        Runs through the specific directory, looking for the files identified with `identifier`. Executes
        the doctests in those files

        Args:
            directory (`Path`): Directory containing the files
            identifier (`str`): Will parse files containing this
            ignore_files (`List[str]`): List of files to skip
            n_identifier (`str` or `List[str]`): Will not parse files containing this/these identifiers.
            only_modules (`bool`): Whether to only analyze modules
        """
        files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]

        if identifier is not None:
            files = [file for file in files if identifier in file]

        if n_identifier is not None:
            if isinstance(n_identifier, list):
                for n_ in n_identifier:
                    files = [file for file in files if n_ not in file]
            else:
                files = [file for file in files if n_identifier not in file]

        ignore_files = ignore_files or []
        ignore_files.append("__init__.py")
        files = [file for file in files if file not in ignore_files]

        for file in files:
            # Open all files
            print("Testing", file)

            if only_modules:
                module_identifier = file.split(".")[0]
                try:
                    module_identifier = getattr(transformers, module_identifier)
                    suite = doctest.DocTestSuite(module_identifier)
                    result = unittest.TextTestRunner().run(suite)
                    self.assertIs(len(result.failures), 0)
                except AttributeError:
                    logger.info(f"{module_identifier} is not a module.")
            else:
                result = doctest.testfile(str(".." / directory / file), optionflags=doctest.ELLIPSIS)
                self.assertIs(result.failed, 0)