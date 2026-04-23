def update_ejs(verify: bool = False) -> dict[str, tuple[str | None, str | None]] | None:
    PACKAGE_NAME = 'yt-dlp-ejs'
    PREFIX = f'    "{PACKAGE_NAME}=='
    LIBRARY_NAME = PACKAGE_NAME.replace('-', '_')
    PACKAGE_PATH = BASE_PATH / 'yt_dlp/extractor/youtube/jsc/_builtin/vendor'

    current_version = None
    with PYPROJECT_PATH.open() as file:
        for line in file:
            if not line.startswith(PREFIX):
                continue
            current_version, _, _ = line.removeprefix(PREFIX).partition('"')

    if not current_version:
        raise ValueError(f'{PACKAGE_NAME} dependency line could not be found')

    makefile_info = ejs_makefile_variables(keys_only=True)
    prefixes = tuple(f'{key} = ' for key in makefile_info)
    with MAKEFILE_PATH.open() as file:
        for line in file:
            if not line.startswith(prefixes):
                continue
            key, _, val = line.partition(' = ')
            makefile_info[key] = val.rstrip()

    info = fetch_latest_github_release('yt-dlp', 'ejs')
    version = info['tag_name']
    if version == current_version:
        print(f'{PACKAGE_NAME} is up to date! ({version})', file=sys.stderr)
        return

    print(f'Updating {PACKAGE_NAME} from {current_version} to {version}', file=sys.stderr)
    hashes = []
    wheel_info = {}
    for asset in info['assets']:
        name = asset['name']
        digest = asset['digest']

        is_wheel = name.startswith(f'{LIBRARY_NAME}-') and name.endswith('.whl')
        if not is_wheel and name not in EJS_ASSETS:
            continue

        with request(asset['browser_download_url']) as resp:
            data = resp.read()

        # verify digest from github
        algo, _, expected = digest.partition(':')
        hexdigest = hashlib.new(algo, data).hexdigest()
        if hexdigest != expected:
            raise ValueError(f'downloaded attest mismatch ({hexdigest!r} != {expected!r})')

        if is_wheel:
            wheel_info = ejs_makefile_variables(version=version, name=name, digest=digest, data=data)
            continue

        # calculate sha3-512 digest
        asset_hash = hashlib.sha3_512(data).hexdigest()
        hashes.append(f'    {name!r}: {asset_hash!r},')

        if EJS_ASSETS[name]:
            (PACKAGE_PATH / name).write_bytes(data)

    hash_mapping = '\n'.join(hashes)
    if missing_assets := [asset_name for asset_name in EJS_ASSETS if asset_name not in hash_mapping]:
        raise ValueError(f'asset(s) not found in release: {", ".join(missing_assets)}')

    if missing_fields := [key for key in makefile_info if not wheel_info.get(key)]:
        raise ValueError(f'wheel info not found in release: {", ".join(missing_fields)}')

    (PACKAGE_PATH / '_info.py').write_text(EJS_TEMPLATE.format(
        version=version,
        hash_mapping=hash_mapping,
    ))

    content = PYPROJECT_PATH.read_text()
    updated = content.replace(PREFIX + current_version, PREFIX + version)
    PYPROJECT_PATH.write_text(updated)

    makefile = MAKEFILE_PATH.read_text()
    for key in wheel_info:
        makefile = makefile.replace(f'{key} = {makefile_info[key]}', f'{key} = {wheel_info[key]}')
    MAKEFILE_PATH.write_text(makefile)

    return update_requirements(upgrade_only=PACKAGE_NAME, verify=verify)