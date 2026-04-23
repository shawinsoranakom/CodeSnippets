def validate_path_safety(path_or_url, user):
    from toolbox import get_conf, default_user_name
    from toolbox import FriendlyException
    PATH_PRIVATE_UPLOAD, PATH_LOGGING = get_conf('PATH_PRIVATE_UPLOAD', 'PATH_LOGGING')
    sensitive_path = None
    path_or_url = os.path.relpath(path_or_url)
    if path_or_url.startswith(PATH_LOGGING):    # 日志文件（按用户划分）
        sensitive_path = PATH_LOGGING
    elif path_or_url.startswith(PATH_PRIVATE_UPLOAD):   # 用户的上传目录（按用户划分）
        sensitive_path = PATH_PRIVATE_UPLOAD
    elif path_or_url.startswith('tests') or path_or_url.startswith('build'):   # 一个常用的测试目录
        return True
    else:
        raise FriendlyException(f"输入文件的路径 ({path_or_url}) 存在，但位置非法。请将文件上传后再执行该任务。") # return False
    if sensitive_path:
        allowed_users = [user, 'autogen', 'arxiv_cache', default_user_name]  # three user path that can be accessed
        for user_allowed in allowed_users:
            if f"{os.sep}".join(path_or_url.split(os.sep)[:2]) == os.path.join(sensitive_path, user_allowed):
                return True
        raise FriendlyException(f"输入文件的路径 ({path_or_url}) 存在，但属于其他用户。请将文件上传后再执行该任务。") # return False
    return True