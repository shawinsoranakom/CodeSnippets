def get_docs_version(version=None):
    version = get_complete_version(version)
    if version[3] != "final":
        return "dev"
    else:
        return "%d.%d" % version[:2]