def test_build_image_from_repo(docker_runtime_builder, tmp_path):
    context_path = str(tmp_path)
    tags = ['alpine:latest']

    # Create a minimal Dockerfile in the context path
    with open(os.path.join(context_path, 'Dockerfile'), 'w') as f:
        f.write(f"""FROM {DEFAULT_BASE_IMAGE}
CMD ["sh", "-c", "echo 'Hello, World!'"]
""")
    built_image_name = None
    container = None
    client = docker.from_env()
    try:
        built_image_name = docker_runtime_builder.build(
            context_path,
            tags,
            use_local_cache=False,
        )
        assert built_image_name == f'{tags[0]}'

        image = client.images.get(tags[0])
        assert image is not None

    except docker.errors.ImageNotFound:
        pytest.fail('test_build_image_from_repo: test image not found!')

    finally:
        # Clean up the container
        if container:
            try:
                container.remove(force=True)
                logger.info(f'Removed test container: `{container.id}`')
            except Exception as e:
                logger.warning(
                    f'Failed to remove test container `{container.id}`: {str(e)}'
                )

        # Clean up the image
        if built_image_name:
            try:
                client.images.remove(built_image_name, force=True)
                logger.info(f'Removed test image: `{built_image_name}`')
            except Exception as e:
                logger.warning(
                    f'Failed to remove test image `{built_image_name}`: {str(e)}'
                )
        else:
            logger.warning('No image was built, so no image cleanup was necessary.')