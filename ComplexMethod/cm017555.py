def post_process(self, paths, dry_run=False, **options):
        """
        Post process the given dictionary of files (called from collectstatic).

        Processing is actually two separate operations:

        1. renaming files to include a hash of their content for cache-busting,
           and copying those files to the target storage.
        2. adjusting files which contain references to other files so they
           refer to the cache-busting filenames.

        If either of these are performed on a file, then that file is
        considered post-processed.
        """
        # don't even dare to process the files if we're in dry run mode
        if dry_run:
            return

        # where to store the new paths
        hashed_files = {}

        # build a list of adjustable files
        adjustable_paths = [
            path for path in paths if matches_patterns(path, self._patterns)
        ]

        # Adjustable files to yield at end, keyed by the original path.
        processed_adjustable_paths = {}

        # Do a single pass first. Post-process all files once, yielding not
        # adjustable files and exceptions, and collecting adjustable files.
        for name, hashed_name, processed, _ in self._post_process(
            paths, adjustable_paths, hashed_files
        ):
            if name not in adjustable_paths or isinstance(processed, Exception):
                yield name, hashed_name, processed
            else:
                processed_adjustable_paths[name] = (name, hashed_name, processed)

        paths = {path: paths[path] for path in adjustable_paths}
        unresolved_paths = []
        for i in range(self.max_post_process_passes):
            unresolved_paths = []
            for name, hashed_name, processed, subst in self._post_process(
                paths, adjustable_paths, hashed_files
            ):
                # Overwrite since hashed_name may be newer.
                processed_adjustable_paths[name] = (name, hashed_name, processed)
                if subst:
                    unresolved_paths.append(name)

            if not unresolved_paths:
                break

        if unresolved_paths:
            problem_paths = ", ".join(sorted(unresolved_paths))
            yield problem_paths, None, RuntimeError("Max post-process passes exceeded.")

        # Store the processed paths
        self.hashed_files.update(hashed_files)

        # Yield adjustable files with final, hashed name.
        yield from processed_adjustable_paths.values()