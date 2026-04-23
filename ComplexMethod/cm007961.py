def makefile_variables(
    prefix: str,
    filetypes: list[str] | None = None,
    *,
    version: str | None = None,
    name: str | None = None,
    digest: str | None = None,
    data: bytes | None = None,
    keys_only: bool = False,
) -> dict[str, str | None]:

    variables = {
        f'{prefix}_VERSION': version,
        f'{prefix}_WHEEL_NAME': name,
        f'{prefix}_WHEEL_HASH': digest,
    }
    for ft in filetypes or []:
        variables.update({
            f'{prefix}_{ft.upper()}_FOLDERS': None,
            f'{prefix}_{ft.upper()}_FILES': None,
        })

    if keys_only:
        return variables

    if not all(arg is not None for arg in (version, name, digest, not filetypes or data)):
        raise ValueError(
            'makefile_variables requires version, name, digest, '
            f'{"and data, " if filetypes else ""}OR keys_only=True')

    if filetypes:
        with io.BytesIO(data) as buf, zipfile.ZipFile(buf) as zipf:
            for ft in filetypes:
                files, folders = zipf_files_and_folders(zipf, f'*.{ft.lower()}')
                variables[f'{prefix}_{ft.upper()}_FOLDERS'] = ' '.join(folders)
                variables[f'{prefix}_{ft.upper()}_FILES'] = ' '.join(files)

    return variables