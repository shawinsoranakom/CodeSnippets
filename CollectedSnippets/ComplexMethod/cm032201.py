def _find_packages(root):
    """
    Helper for ``build_index()``: Yield a list of tuples
    ``(pkg_xml, zf, subdir)``, where:
      - ``pkg_xml`` is an ``ElementTree.Element`` holding the xml for a
        package
      - ``zf`` is a ``zipfile.ZipFile`` for the package's contents.
      - ``subdir`` is the subdirectory (relative to ``root``) where
        the package was found (e.g. 'corpora' or 'grammars').
    """
    from nltk.corpus.reader.util import _path_from

    # Find all packages.
    packages = []
    for dirname, subdirs, files in os.walk(root):
        relpath = "/".join(_path_from(root, dirname))
        for filename in files:
            if filename.endswith(".xml"):
                xmlfilename = os.path.join(dirname, filename)
                zipfilename = xmlfilename[:-4] + ".zip"
                try:
                    zf = zipfile.ZipFile(zipfilename)
                except Exception as e:
                    raise ValueError(f"Error reading file {zipfilename!r}!\n{e}") from e
                try:
                    pkg_xml = ElementTree.parse(xmlfilename).getroot()
                except Exception as e:
                    raise ValueError(f"Error reading file {xmlfilename!r}!\n{e}") from e

                # Check that the UID matches the filename
                uid = os.path.split(xmlfilename[:-4])[1]
                if pkg_xml.get("id") != uid:
                    raise ValueError(
                        "package identifier mismatch (%s "
                        "vs %s)" % (pkg_xml.get("id"), uid)
                    )

                # Check that the zipfile expands to a subdir whose
                # name matches the uid.
                if sum(
                    (name != uid and not name.startswith(uid + "/"))
                    for name in zf.namelist()
                ):
                    raise ValueError(
                        "Zipfile %s.zip does not expand to a "
                        "single subdirectory %s/" % (uid, uid)
                    )

                yield pkg_xml, zf, relpath

            elif filename.endswith(".zip"):
                # Warn user in case a .xml does not exist for a .zip
                resourcename = os.path.splitext(filename)[0]
                xmlfilename = os.path.join(dirname, resourcename + ".xml")
                if not os.path.exists(xmlfilename):
                    warnings.warn(
                        f"{filename} exists, but {resourcename + '.xml'} cannot be found! "
                        f"This could mean that {resourcename} can not be downloaded.",
                        stacklevel=2,
                    )

        # Don't recurse into svn subdirectories:
        try:
            subdirs.remove(".svn")
        except ValueError:
            pass