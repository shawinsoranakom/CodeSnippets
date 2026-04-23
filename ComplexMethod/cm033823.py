def main():
    """Entrypoint to the script"""

    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    bundled_libs = get_bundled_libs(paths)
    files_with_bundled_metadata = get_files_with_bundled_metadata(paths)

    for filename in files_with_bundled_metadata.difference(bundled_libs):
        if filename.startswith('test/support/'):
            continue  # bundled support code does not need to be updated or tracked

        print(f'{filename}: ERROR: File contains _BUNDLED_METADATA but needs to be added to test/sanity/code-smell/update-bundled.py')

    for filename in bundled_libs:
        try:
            metadata = get_bundled_metadata(filename)
        except ValueError as e:
            print(f'{filename}: ERROR: {e}')
            continue
        except OSError as e:
            if e.errno == 2:
                print(
                    f'{filename}: ERROR: {e}. '
                    'Perhaps the bundled library has been removed or moved and the bundled library test needs to be modified as well?'
                )

        if metadata is None:
            continue

        pypi_fh = open_url('https://pypi.org/pypi/{0}/json'.format(metadata['pypi_name']))
        pypi_data = json.loads(pypi_fh.read().decode('utf-8'))

        constraints = metadata.get('version_constraints', None)
        latest_version = get_latest_applicable_version(pypi_data, constraints)

        if LooseVersion(metadata['version']) < LooseVersion(latest_version):
            name = metadata['pypi_name']
            version = metadata['version']
            url = f"https://pypi.org/pypi/{name}/json"

            print(f"{filename}: UPDATE {name} from {version} to {latest_version} {url}")