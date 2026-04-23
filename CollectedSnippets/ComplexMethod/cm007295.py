def sanitize_path(s):
    """Sanitizes and normalizes path on Windows"""
    if sys.platform != 'win32':
        return s
    drive_or_unc, _ = os.path.splitdrive(s)
    if sys.version_info < (2, 7) and not drive_or_unc:
        drive_or_unc, _ = os.path.splitunc(s)
    norm_path = os.path.normpath(remove_start(s, drive_or_unc)).split(os.path.sep)
    if drive_or_unc:
        norm_path.pop(0)
    sanitized_path = [
        path_part if path_part in ['.', '..'] else re.sub(r'(?:[/<>:"\|\\?\*]|[\s.]$)', '#', path_part)
        for path_part in norm_path]
    if drive_or_unc:
        sanitized_path.insert(0, drive_or_unc + os.path.sep)
    return os.path.join(*sanitized_path)