def converter(matchobj):
            """
            Convert the matched URL to a normalized and hashed URL.

            This requires figuring out which files the matched URL resolves
            to and calling the url() method of the storage.
            """
            matches = matchobj.groupdict()
            matched = matches["matched"]
            url = matches["url"]

            # Ignore URLs in comments.
            if comment_blocks and self.is_in_comment(matchobj.start(), comment_blocks):
                return matched

            # Ignore absolute/protocol-relative and data-uri URLs.
            if re.match(r"^[a-z]+:", url) or url.startswith("//"):
                return matched

            # Ignore absolute URLs that don't point to a static file (dynamic
            # CSS / JS?). Note that STATIC_URL cannot be empty.
            if url.startswith("/") and not url.startswith(settings.STATIC_URL):
                return matched

            # Strip off the fragment so a path-like fragment won't interfere.
            url_path, fragment = urldefrag(url)

            # Ignore URLs without a path
            if not url_path:
                return matched

            if url_path.startswith("/"):
                # Otherwise the condition above would have returned
                # prematurely.
                assert url_path.startswith(settings.STATIC_URL)
                target_name = url_path.removeprefix(settings.STATIC_URL)
            else:
                # We're using the posixpath module to mix paths and URLs
                # conveniently.
                source_name = name if os.sep == "/" else name.replace(os.sep, "/")
                target_name = posixpath.join(posixpath.dirname(source_name), url_path)

            # Determine the hashed name of the target file with the storage
            # backend.
            try:
                hashed_url = self._url(
                    self._stored_name,
                    unquote(target_name),
                    force=True,
                    hashed_files=hashed_files,
                )
            except ValueError as exc:
                line = _line_at_position(matchobj.string, matchobj.start())
                note = f"{name!r} contains this reference {matched!r} on line {line}"
                exc.add_note(note)
                raise exc

            transformed_url = "/".join(
                url_path.split("/")[:-1] + hashed_url.split("/")[-1:]
            )

            # Restore the fragment that was stripped off earlier.
            if fragment:
                transformed_url += ("?#" if "?#" in url else "#") + fragment

            # Return the hashed version to the file
            matches["url"] = unquote(transformed_url)
            return template % matches