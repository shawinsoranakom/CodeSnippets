def _get_functions(overridden):
    proc = Popen(['fish', '-ic', 'functions'], stdout=PIPE, stderr=DEVNULL)
    functions = proc.stdout.read().decode('utf-8').strip().split('\n')
    return {func: func for func in functions if func not in overridden}