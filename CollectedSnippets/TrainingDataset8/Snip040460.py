def verify_pep440(version):
    """Verify if version is PEP440 compliant.

    https://github.com/pypa/packaging/blob/16.7/packaging/version.py#L191

    We might need pre, post, alpha, rc in the future so might as well
    use an object that does all that.  This verifies its a valid
    version.
    """

    try:
        return packaging.version.Version(version)
    except packaging.version.InvalidVersion as e:
        raise (e)