def _main():
    "Print module output (default this file) for quick visual check."
    import os
    try:
        mod = sys.argv[1]
    except:
        mod = __file__
    if os.path.exists(mod):
        path = [os.path.dirname(mod)]
        mod = os.path.basename(mod)
        if mod.lower().endswith(".py"):
            mod = mod[:-3]
    else:
        path = []
    tree = readmodule_ex(mod, path)
    lineno_key = lambda a: getattr(a, 'lineno', 0)
    objs = sorted(tree.values(), key=lineno_key, reverse=True)
    indent_level = 2
    while objs:
        obj = objs.pop()
        if isinstance(obj, list):
            # Value is a __path__ key.
            continue
        if not hasattr(obj, 'indent'):
            obj.indent = 0

        if isinstance(obj, _Object):
            new_objs = sorted(obj.children.values(),
                              key=lineno_key, reverse=True)
            for ob in new_objs:
                ob.indent = obj.indent + indent_level
            objs.extend(new_objs)
        if isinstance(obj, Class):
            print("{}class {} {} {}"
                  .format(' ' * obj.indent, obj.name, obj.super, obj.lineno))
        elif isinstance(obj, Function):
            print("{}def {} {}".format(' ' * obj.indent, obj.name, obj.lineno))