def check_sanitizer(*, address=False, memory=False, ub=False, thread=False,
                    function=True):
    """Returns True if Python is compiled with sanitizer support"""
    if not (address or memory or ub or thread):
        raise ValueError('At least one of address, memory, ub or thread must be True')


    cflags = sysconfig.get_config_var('CFLAGS') or ''
    config_args = sysconfig.get_config_var('CONFIG_ARGS') or ''
    memory_sanitizer = (
        '-fsanitize=memory' in cflags or
        '--with-memory-sanitizer' in config_args
    )
    address_sanitizer = (
        '-fsanitize=address' in cflags or
        '--with-address-sanitizer' in config_args
    )
    ub_sanitizer = (
        '-fsanitize=undefined' in cflags or
        '--with-undefined-behavior-sanitizer' in config_args
    )
    thread_sanitizer = (
        '-fsanitize=thread' in cflags or
        '--with-thread-sanitizer' in config_args
    )
    function_sanitizer = (
        '-fsanitize=function' in cflags
    )
    return (
        (memory and memory_sanitizer) or
        (address and address_sanitizer) or
        (ub and ub_sanitizer) or
        (thread and thread_sanitizer) or
        (function and function_sanitizer)
    )