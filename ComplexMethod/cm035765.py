def test_generate_dockerfile_build_from_scratch():
    base_image = 'debian:11'
    dockerfile_content = _generate_dockerfile(
        base_image,
        build_from=BuildFromImageType.SCRATCH,
    )
    assert base_image in dockerfile_content
    assert 'apt-get update' in dockerfile_content
    assert 'wget curl' in dockerfile_content
    assert 'poetry' in dockerfile_content and '-c conda-forge' in dockerfile_content
    assert 'python=3.12' in dockerfile_content

    # Check the update command
    assert (
        'COPY --chown=openhands:openhands ./code/openhands /openhands/code/openhands'
        in dockerfile_content
    )
    assert (
        '/openhands/micromamba/bin/micromamba run -n openhands poetry install'
        in dockerfile_content
    )