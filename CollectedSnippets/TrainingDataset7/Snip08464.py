def save(self, name, content, max_length=None):
        """
        Save new content to the file specified by name. The content should be
        a proper File object or any Python file-like object, ready to be read
        from the beginning.
        """
        # Get the proper name for the file, as it will actually be saved.
        if name is None:
            name = content.name

        if not hasattr(content, "chunks"):
            content = File(content, name)

        # Ensure that the name is valid, before and after having the storage
        # system potentially modifying the name. This duplicates the check made
        # inside `get_available_name` but it's necessary for those cases where
        # `get_available_name` is overridden and validation is lost.
        validate_file_name(name, allow_relative_path=True)

        # Potentially find a different name depending on storage constraints.
        name = self.get_available_name(name, max_length=max_length)
        # Validate the (potentially) new name.
        validate_file_name(name, allow_relative_path=True)

        # The save operation should return the actual name of the file saved.
        name = self._save(name, content)
        # Ensure that the name returned from the storage system is still valid.
        validate_file_name(name, allow_relative_path=True)
        return name