def copytree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))