def stored_name(self, name):
        cleaned_name = self.clean_name(name)
        hash_key = self.hash_key(cleaned_name)
        cache_name = self.hashed_files.get(hash_key)
        if cache_name:
            return cache_name
        # No cached name found, recalculate it from the files.
        intermediate_name = name
        for i in range(self.max_post_process_passes + 1):
            cache_name = self.clean_name(
                self.hashed_name(name, content=None, filename=intermediate_name)
            )
            if intermediate_name == cache_name:
                # Store the hashed name if there was a miss.
                self.hashed_files[hash_key] = cache_name
                return cache_name
            else:
                # Move on to the next intermediate file.
                intermediate_name = cache_name
        # If the cache name can't be determined after the max number of passes,
        # the intermediate files on disk may be corrupt; avoid an infinite
        # loop.
        raise ValueError("The name '%s' could not be hashed with %r." % (name, self))