def __docker_pull(args: CommonConfig, image: str) -> None:
    """Internal implementation for docker_pull. Do not call directly."""
    if '@' not in image and ':' not in image:
        display.info('Skipping pull of image without tag or digest: %s' % image, verbosity=2)
        docker_image_inspect(args, image)
    elif docker_image_inspect(args, image, always=True):
        display.info('Skipping pull of existing image: %s' % image, verbosity=2)
    else:
        for _iteration in range(1, 10):
            try:
                docker_command(args, ['pull', image], capture=False)

                if docker_image_inspect(args, image) or args.explain:
                    break

                display.warning(f'Image "{image}" not found after pull completed. Waiting a few seconds before trying again.')
            except SubprocessError:
                display.warning(f'Failed to pull container image "{image}". Waiting a few seconds before trying again.')
                time.sleep(3)
        else:
            raise ApplicationError(f'Failed to pull container image "{image}".')