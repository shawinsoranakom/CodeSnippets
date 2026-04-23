def extract_archive(file_path, dest_dir):
    import zipfile
    import tarfile
    import os

    # Get the file extension of the input file
    file_extension = os.path.splitext(file_path)[1]

    # Extract the archive based on its extension
    if file_extension == ".zip":
        with zipfile.ZipFile(file_path, "r") as zipobj:
            zipobj._extract_member = lambda a,b,c: zip_extract_member_new(zipobj, a,b,c)    # 修复中文乱码的问题
            zipobj.extractall(path=dest_dir)
            logger.info("Successfully extracted zip archive to {}".format(dest_dir))

    elif file_extension in [".tar", ".gz", ".bz2"]:
        try:
            with tarfile.open(file_path, "r:*") as tarobj:
                # 清理提取路径，移除任何不安全的元素
                for member in tarobj.getmembers():
                    member_path = os.path.normpath(member.name)
                    full_path = os.path.join(dest_dir, member_path)
                    full_path = os.path.abspath(full_path)
                    if member.islnk() or member.issym():
                        raise Exception(f"Attempted Symlink in {member.name}")
                    if not full_path.startswith(os.path.abspath(dest_dir) + os.sep):
                        raise Exception(f"Attempted Path Traversal in {member.name}")

                tarobj.extractall(path=dest_dir)
                logger.info("Successfully extracted tar archive to {}".format(dest_dir))
        except tarfile.ReadError as e:
            if file_extension == ".gz":
                # 一些特别奇葩的项目，是一个gz文件，里面不是tar，只有一个tex文件
                import gzip
                with gzip.open(file_path, 'rb') as f_in:
                    with open(os.path.join(dest_dir, 'main.tex'), 'wb') as f_out:
                        f_out.write(f_in.read())
            else:
                raise e

    # 第三方库，需要预先pip install rarfile
    # 此外，Windows上还需要安装winrar软件，配置其Path环境变量，如"C:\Program Files\WinRAR"才可以
    elif file_extension == ".rar":
        try:
            import rarfile  # 用来检查rarfile是否安装，不要删除
            safe_extract_rar(file_path, dest_dir)
        except:
            logger.info("Rar format requires additional dependencies to install")
            return "<br/><br/>解压失败! 需要安装pip install rarfile来解压rar文件。建议：使用zip压缩格式。"

    # 第三方库，需要预先pip install py7zr
    elif file_extension == ".7z":
        try:
            import py7zr

            with py7zr.SevenZipFile(file_path, mode="r") as f:
                f.extractall(path=dest_dir)
                logger.info("Successfully extracted 7z archive to {}".format(dest_dir))
        except:
            logger.info("7z format requires additional dependencies to install")
            return "<br/><br/>解压失败! 需要安装pip install py7zr来解压7z文件"
    else:
        return ""
    return ""