def load_zip_file(file, fileNameRegExp="", allEntries=False):
    """
    Returns an array with the contents (filtered by fileNameRegExp) of a ZIP file.
    The key's are the names or the file or the capturing group defined in the fileNameRegExp
    allEntries validates that all entries in the ZIP file pass the fileNameRegExp
    """
    try:
        archive = zipfile.ZipFile(file, mode="r", allowZip64=True)
    except:
        raise Exception("Error loading the ZIP archive")

    pairs = []
    for name in archive.namelist():
        addFile = True
        keyName = name
        if fileNameRegExp != "":
            m = re.match(fileNameRegExp, name)
            if m == None:
                addFile = False
            else:
                if len(m.groups()) > 0:
                    keyName = m.group(1)

        if addFile:
            pairs.append([keyName, archive.read(name)])
        else:
            if allEntries:
                raise Exception("ZIP entry not valid: %s" % name)

    return dict(pairs)