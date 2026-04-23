def zip_extract_member_new(self, member, targetpath, pwd):
    # 修复中文乱码的问题
    """Extract the ZipInfo object 'member' to a physical
        file on the path targetpath.
    """
    import zipfile
    if not isinstance(member, zipfile.ZipInfo):
        member = self.getinfo(member)

    # build the destination pathname, replacing
    # forward slashes to platform specific separators.
    arcname = member.filename.replace('/', os.path.sep)
    arcname = arcname.encode('cp437', errors='replace').decode('gbk', errors='replace')

    if os.path.altsep:
        arcname = arcname.replace(os.path.altsep, os.path.sep)
    # interpret absolute pathname as relative, remove drive letter or
    # UNC path, redundant separators, "." and ".." components.
    arcname = os.path.splitdrive(arcname)[1]
    invalid_path_parts = ('', os.path.curdir, os.path.pardir)
    arcname = os.path.sep.join(x for x in arcname.split(os.path.sep)
                                if x not in invalid_path_parts)
    if os.path.sep == '\\':
        # filter illegal characters on Windows
        arcname = self._sanitize_windows_name(arcname, os.path.sep)

    targetpath = os.path.join(targetpath, arcname)
    targetpath = os.path.normpath(targetpath)

    # Create all upper directories if necessary.
    upperdirs = os.path.dirname(targetpath)
    if upperdirs and not os.path.exists(upperdirs):
        os.makedirs(upperdirs)

    if member.is_dir():
        if not os.path.isdir(targetpath):
            os.mkdir(targetpath)
        return targetpath

    with self.open(member, pwd=pwd) as source, \
            open(targetpath, "wb") as target:
        shutil.copyfileobj(source, target)

    return targetpath