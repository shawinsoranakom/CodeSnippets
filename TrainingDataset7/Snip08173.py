def stored_name(self, name):
        parsed_name = urlsplit(unquote(name))
        clean_name = parsed_name.path.strip()
        hash_key = self.hash_key(clean_name)
        cache_name = self.hashed_files.get(hash_key)
        if cache_name is None:
            if self.manifest_strict:
                raise ValueError(
                    "Missing staticfiles manifest entry for '%s'" % clean_name
                )
            cache_name = self.clean_name(self.hashed_name(name))
        unparsed_name = list(parsed_name)
        unparsed_name[2] = cache_name
        # Special casing for a @font-face hack, like url(myfont.eot?#iefix")
        # http://www.fontspring.com/blog/the-new-bulletproof-font-face-syntax
        if "?#" in name and not unparsed_name[3]:
            unparsed_name[2] += "?"
        return urlunsplit(unparsed_name)