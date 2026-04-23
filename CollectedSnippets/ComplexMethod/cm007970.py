def get_target(root: dict, paths: list[str], is_list=False):
    target = root

    for index, key in enumerate(paths, 1):
        use_list = is_list and index == len(paths)
        result = target.get(key)
        if result is None:
            result = [] if use_list else {}
            target[key] = result

        if isinstance(result, dict):
            target = result
        elif use_list:
            target = {}
            result.append(target)
        else:
            target = result[-1]

    assert isinstance(target, dict)
    return target