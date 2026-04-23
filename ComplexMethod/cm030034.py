def makelink_with_filter(self, tarinfo, targetpath,
                             filter_function, extraction_root):
        """Make a (symbolic) link called targetpath. If it cannot be created
          (platform limitation), we try to make a copy of the referenced file
          instead of a link.

          filter_function is only used when extracting a *different*
          member (e.g. as fallback to creating a link).
        """
        keyerror_to_extracterror = False
        try:
            # For systems that support symbolic and hard links.
            if tarinfo.issym():
                if os.path.lexists(targetpath):
                    # Avoid FileExistsError on following os.symlink.
                    os.unlink(targetpath)
                link_target = tarinfo.linkname
                if os.name == "nt":
                    # gh-57911: Posix-flavoured forward-slash path separators in
                    # symlink targets aren't acknowledged by Windows, resulting
                    # in corrupted links.
                    link_target = link_target.replace("/", os.path.sep)
                os.symlink(link_target, targetpath)
                return
            else:
                if os.path.exists(tarinfo._link_target):
                    if os.path.lexists(targetpath):
                        # Avoid FileExistsError on following os.link.
                        os.unlink(targetpath)
                    os.link(tarinfo._link_target, targetpath)
                    return
        except symlink_exception:
            keyerror_to_extracterror = True

        try:
            unfiltered = self._find_link_target(tarinfo)
        except KeyError:
            if keyerror_to_extracterror:
                raise ExtractError(
                    "unable to resolve link inside archive") from None
            else:
                raise

        if filter_function is None:
            filtered = unfiltered
        else:
            if extraction_root is None:
                raise ExtractError(
                    "makelink_with_filter: if filter_function is not None, "
                    + "extraction_root must also not be None")
            try:
                filtered = filter_function(unfiltered, extraction_root)
            except _FILTER_ERRORS as cause:
                raise LinkFallbackError(tarinfo, unfiltered.name) from cause
        if filtered is not None:
            self._extract_member(filtered, targetpath,
                                 filter_function=filter_function,
                                 extraction_root=extraction_root)