def wrapper(*args, **kwargs):
        return safety_marker(func(*args, **kwargs))