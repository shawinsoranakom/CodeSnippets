def _isdir(part):
    return not part.startswith('-') and os.path.isdir(part)