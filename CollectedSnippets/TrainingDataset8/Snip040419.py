def main():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE) as f:
            print(f.read())
            return

    if len(sys.argv) != 2:
        raise Exception(
            'Specify target version as an argument: "%s 1.2.3"' % sys.argv[0]
        )

    target_version = semver.VersionInfo.parse(sys.argv[1])
    # Ensure that current version is semver-compliant (it's stored as PEP440-compliant in setup.py)
    current_version = semver.VersionInfo.parse(
        get_current_version().replace("rc", "-rc.")
    )

    if current_version.finalize_version() < target_version:
        current_version = target_version

    new_version = str(current_version.bump_prerelease())
    with open(VERSION_FILE, "w") as f:
        f.write(new_version)

    print(new_version)