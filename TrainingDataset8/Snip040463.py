def main():
    """Run main loop."""

    if len(sys.argv) != 2:
        e = Exception(
            'Specify semvver version as an argument, e.g.: "%s 1.2.3"' % sys.argv[0]
        )
        raise (e)

    # We need two flavors of the version - one that's semver-compliant for Node, one that's
    # PEP440-compliant for Python. We allow for the incoming version to be either semver-compliant
    # PEP440-compliant.
    # - `verify_pep440` automatically converts semver to PEP440-compliant
    pep440_version = verify_pep440(sys.argv[1])

    # - Attempt to convert to semver-compliant. If a failure occurs, manually attempt to convert.
    semver_version = None
    try:
        semver_version = verify_semver(sys.argv[1])
    except ValueError:
        semver_version = verify_semver(
            sys.argv[1].replace("rc", "-rc.").replace(".dev", "-dev")
        )

    update_files(PYTHON, pep440_version)
    update_files(NODE, semver_version)