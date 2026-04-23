def setup_variables(environment):
    """
    `environment` must contain these keys:
        REPOSITORY, INPUTS, PROCESSED, PYPI_PROJECT,
        SOURCE_PYPI_PROJECT, SOURCE_PYPI_SUFFIX,
        TARGET_PYPI_PROJECT, TARGET_PYPI_SUFFIX,
        SOURCE_ARCHIVE_REPO, TARGET_ARCHIVE_REPO,
        HAS_ARCHIVE_REPO_TOKEN, HAS_RELEASE_KEY

    `INPUTS` must contain these keys:
        prerelease

    `PROCESSED` must contain these keys:
        source_repo, source_tag,
        target_repo, target_tag
    """
    REPOSITORY = environment['REPOSITORY']
    INPUTS = json.loads(environment['INPUTS'])
    PROCESSED = json.loads(environment['PROCESSED'])

    source_channel = None
    pypi_project = None
    pypi_suffix = None

    source_repo = PROCESSED['source_repo']
    source_tag = PROCESSED['source_tag']
    if source_repo == 'stable':
        source_repo = STABLE_REPOSITORY
    if not source_repo:
        source_repo = REPOSITORY
    elif environment['SOURCE_ARCHIVE_REPO']:
        source_channel = environment['SOURCE_ARCHIVE_REPO']
    elif not source_tag and '/' not in source_repo:
        source_tag = source_repo
        source_repo = REPOSITORY

    resolved_source = source_repo
    if source_tag:
        resolved_source = f'{resolved_source}@{source_tag}'
    elif source_repo == STABLE_REPOSITORY:
        resolved_source = 'stable'

    revision = None
    if INPUTS['prerelease'] or not json.loads(environment['HAS_RELEASE_KEY']):
        revision = dt.datetime.now(tz=dt.timezone.utc).strftime('%H%M%S')

    version = calculate_version(INPUTS.get('version') or revision)

    target_repo = PROCESSED['target_repo']
    target_tag = PROCESSED['target_tag']
    if target_repo:
        if target_repo == 'stable':
            target_repo = STABLE_REPOSITORY
        if not target_tag:
            if target_repo == STABLE_REPOSITORY:
                target_tag = version
            elif environment['TARGET_ARCHIVE_REPO']:
                target_tag = source_tag or version
            else:
                target_tag = target_repo
                target_repo = REPOSITORY
        if target_repo != REPOSITORY:
            target_repo = environment['TARGET_ARCHIVE_REPO']
            pypi_project = environment['TARGET_PYPI_PROJECT'] or None
            pypi_suffix = environment['TARGET_PYPI_SUFFIX'] or None
    else:
        target_tag = source_tag or version
        if source_channel:
            target_repo = source_channel
            pypi_project = environment['SOURCE_PYPI_PROJECT'] or None
            pypi_suffix = environment['SOURCE_PYPI_SUFFIX'] or None
        else:
            target_repo = REPOSITORY

    if target_repo != REPOSITORY and not json.loads(environment['HAS_ARCHIVE_REPO_TOKEN']):
        return None

    if target_repo == REPOSITORY and not INPUTS['prerelease']:
        pypi_project = environment['PYPI_PROJECT'] or None

    return {
        'channel': resolved_source,
        'version': version,
        'target_repo': target_repo,
        'target_tag': target_tag,
        'pypi_project': pypi_project,
        'pypi_suffix': pypi_suffix,
    }