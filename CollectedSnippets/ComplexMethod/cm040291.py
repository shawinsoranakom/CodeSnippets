def _get_most_recently_modified_file_matching_pattern(self, pattern):
        """Returns the most recently modified filepath matching pattern.

        In the rare case where there are more than one pattern-matching file
        having the same modified time that is most recent among all, return the
        filepath that is largest (by `>` operator, lexicographically using the
        numeric equivalents). This provides a tie-breaker when multiple files
        are most recent. Note that a larger `filepath` can sometimes indicate a
        later time of modification (for instance, when epoch/batch is used as
        formatting option), but not necessarily (when accuracy or loss is used).
        The tie-breaker is put in the logic as best effort to return the most
        recent, and to avoid nondeterministic result.

        Modified time of a file is obtained with `os.path.getmtime()`.

        This utility function is best demonstrated via an example:

        ```python
        file_pattern = 'batch{batch:02d}epoch{epoch:02d}.keras'
        test_dir = self.get_temp_dir()
        path_pattern = os.path.join(test_dir, file_pattern)
        file_paths = [
            os.path.join(test_dir, file_name) for file_name in
            ['batch03epoch02.keras',
             'batch02epoch02.keras', 'batch01epoch01.keras']
        ]
        for file_path in file_paths:
            # Write something to each of the files
            ...
        self.assertEqual(
            _get_most_recently_modified_file_matching_pattern(path_pattern),
            file_paths[-1])
        ```

        Args:
            pattern: The file pattern that may optionally contain python
                placeholder such as `{epoch:02d}`.

        Returns:
            The most recently modified file's full filepath matching `pattern`.
            If `pattern` does not contain any placeholder, this returns the
            filepath that exactly matches `pattern`. Returns `None` if no match
            is found.
        """
        dir_name = os.path.dirname(pattern)
        base_name = os.path.basename(pattern)
        base_name_regex = f"^{re.sub(r'{.*}', r'.*', base_name)}$"

        latest_mod_time = 0
        file_path_with_latest_mod_time = None
        n_file_with_latest_mod_time = 0
        file_path_with_largest_file_name = None

        if file_utils.exists(dir_name):
            for file_name in os.listdir(dir_name):
                # Only consider if `file_name` matches the pattern.
                if re.match(base_name_regex, file_name):
                    file_path = os.path.join(dir_name, file_name)
                    mod_time = os.path.getmtime(file_path)
                    if (
                        file_path_with_largest_file_name is None
                        or file_path > file_path_with_largest_file_name
                    ):
                        file_path_with_largest_file_name = file_path
                    if mod_time > latest_mod_time:
                        latest_mod_time = mod_time
                        file_path_with_latest_mod_time = file_path
                        # In the case a file with later modified time is found,
                        # reset the counter for the number of files with latest
                        # modified time.
                        n_file_with_latest_mod_time = 1
                    elif mod_time == latest_mod_time:
                        # In the case a file has modified time tied with the
                        # most recent, increment the counter for the number of
                        # files with latest modified time by 1.
                        n_file_with_latest_mod_time += 1

        if n_file_with_latest_mod_time == 1:
            # Return the sole file that has most recent modified time.
            return file_path_with_latest_mod_time
        else:
            # If there are more than one file having latest modified time,
            # return the file path with the largest file name.
            return file_path_with_largest_file_name