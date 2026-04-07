def get_branch(version, next_version):
    if version == next_version:
        return "main"
    else:
        return f"stable/{version}.x"