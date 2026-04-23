def docker_image_inspect(args: CommonConfig, image: str, always: bool = False) -> t.Optional[DockerImageInspect]:
    """
    Return the results of `docker image inspect` for the specified image or None if the image does not exist.
    """
    inspect_cache: dict[str, DockerImageInspect]

    try:
        inspect_cache = docker_image_inspect.cache  # type: ignore[attr-defined]
    except AttributeError:
        inspect_cache = docker_image_inspect.cache = {}  # type: ignore[attr-defined]

    if inspect_result := inspect_cache.get(image):
        return inspect_result

    try:
        stdout = docker_command(args, ['image', 'inspect', image], capture=True, always=always)[0]
    except SubprocessError:
        stdout = '[]'

    if args.explain and not always:
        items = []
    else:
        items = json.loads(stdout)

    if len(items) > 1:
        raise ApplicationError(f'Inspection of image "{image}" resulted in {len(items)} items:\n{json.dumps(items, indent=4)}')

    if len(items) == 1:
        inspect_result = DockerImageInspect(args, items[0])
        inspect_cache[image] = inspect_result
        return inspect_result

    return None