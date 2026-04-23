def _parse_os_release_content(lines: TextIO) -> Dict[str, str]:
        """
        Parse the lines of an os-release file.

        Parameters:

        * lines: Iterable through the lines in the os-release file.
                 Each line must be a unicode string or a UTF-8 encoded byte
                 string.

        Returns:
            A dictionary containing all information items.
        """
        props = {}
        lexer = shlex.shlex(lines, posix=True)
        lexer.whitespace_split = True

        tokens = list(lexer)
        for token in tokens:
            # At this point, all shell-like parsing has been done (i.e.
            # comments processed, quotes and backslash escape sequences
            # processed, multi-line values assembled, trailing newlines
            # stripped, etc.), so the tokens are now either:
            # * variable assignments: var=value
            # * commands or their arguments (not allowed in os-release)
            # Ignore any tokens that are not variable assignments
            if "=" in token:
                k, v = token.split("=", 1)
                props[k.lower()] = v

        if "version" in props:
            # extract release codename (if any) from version attribute
            match = re.search(r"\((\D+)\)|,\s*(\D+)", props["version"])
            if match:
                release_codename = match.group(1) or match.group(2)
                props["codename"] = props["release_codename"] = release_codename

        if "version_codename" in props:
            # os-release added a version_codename field.  Use that in
            # preference to anything else Note that some distros purposefully
            # do not have code names.  They should be setting
            # version_codename=""
            props["codename"] = props["version_codename"]
        elif "ubuntu_codename" in props:
            # Same as above but a non-standard field name used on older Ubuntus
            props["codename"] = props["ubuntu_codename"]

        return props