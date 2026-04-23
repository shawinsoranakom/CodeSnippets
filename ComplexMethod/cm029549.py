def copycleandir(src, dst):
    for cursrc, dirs, files in os.walk(src):
        assert cursrc.startswith(src)
        curdst = dst + cursrc[len(src):]
        if verbose:
            print("mkdir", curdst)
        if not debug:
            if not os.path.exists(curdst):
                os.makedirs(curdst)
        for fn in files:
            if isclean(fn):
                if verbose:
                    print("copy", os.path.join(cursrc, fn), os.path.join(curdst, fn))
                if not debug:
                    shutil.copy2(os.path.join(cursrc, fn), os.path.join(curdst, fn))
            else:
                if verbose:
                    print("skipfile", os.path.join(cursrc, fn))
        for i in range(len(dirs)-1, -1, -1):
            if not isclean(dirs[i]):
                if verbose:
                    print("skipdir", os.path.join(cursrc, dirs[i]))
                del dirs[i]