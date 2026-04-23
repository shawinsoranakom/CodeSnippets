def isclean(name):
    if name in ('CVS', '.cvsignore', '.svn'):
        return 0
    if name.lower() == '.ds_store': return 0
    if name.endswith('~'): return 0
    if name.endswith('.BAK'): return 0
    if name.endswith('.pyc'): return 0
    if name.endswith('.pyo'): return 0
    if name.endswith('.orig'): return 0
    return 1