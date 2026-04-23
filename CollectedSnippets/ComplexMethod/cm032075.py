def find_tex_file_ignore_case(fp):
    dir_name = os.path.dirname(fp)
    base_name = os.path.basename(fp)
    # 如果输入的文件路径是正确的
    if os.path.isfile(pj(dir_name, base_name)):
        return pj(dir_name, base_name)
    # 如果不正确，试着加上.tex后缀试试
    if not base_name.endswith(".tex"):
        base_name += ".tex"
    if os.path.isfile(pj(dir_name, base_name)):
        return pj(dir_name, base_name)
    # 如果还找不到，解除大小写限制，再试一次
    import glob

    for f in glob.glob(dir_name + "/*.tex"):
        base_name_s = os.path.basename(fp)
        base_name_f = os.path.basename(f)
        if base_name_s.lower() == base_name_f.lower():
            return f
        # 试着加上.tex后缀试试
        if not base_name_s.endswith(".tex"):
            base_name_s += ".tex"
        if base_name_s.lower() == base_name_f.lower():
            return f
    return None