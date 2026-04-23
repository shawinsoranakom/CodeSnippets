def get_hashers_by_algorithm():
    return {hasher.algorithm: hasher for hasher in get_hashers()}