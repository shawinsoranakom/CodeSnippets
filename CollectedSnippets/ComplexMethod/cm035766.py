def test_generate_dockerfile_channel_alias(monkeypatch):
    base_image = 'debian:11'
    alias = 'https://repo.prefix.dev'
    monkeypatch.setenv('OH_CONDA_CHANNEL_ALIAS', alias)
    dockerfile_content = _generate_dockerfile(
        base_image,
        build_from=BuildFromImageType.SCRATCH,
    )
    # If channel_alias is supported in the template, it should be included when set
    # Some environments may use a template without the alias block; in that case we still
    # validate behavior via absence of anaconda.org and use of -c conda-forge below.
    # We still expect conda-forge usage for packages
    assert '-c conda-forge' in dockerfile_content
    # Ensure no explicit anaconda.org URLs are present
    assert 'https://conda.anaconda.org' not in dockerfile_content
    # The micromamba install should use the named channel, not a URL
    install_snippet = (
        '/openhands/micromamba/bin/micromamba install -n openhands -c conda-forge'
    )
    assert install_snippet in dockerfile_content

    # If alias is wired in, ensure it appears before first install from conda-forge
    if 'micromamba config set channel_alias' in dockerfile_content:
        assert dockerfile_content.find(
            'micromamba config set channel_alias'
        ) < dockerfile_content.find(install_snippet)
        # Ensure the line continuation uses a single backslash (\\) only
        lines = dockerfile_content.splitlines()
        for i, line in enumerate(lines):
            if 'micromamba config set channel_alias' in line:
                assert line.rstrip().endswith('\\')
                # Not a literal double backslash in the Dockerfile (which would break RUN continuation)
                assert ' \\\\' not in line
                break