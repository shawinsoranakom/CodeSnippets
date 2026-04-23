def _find_paper_file(path: str) -> str:
    """查找路径中的论文文件（简化版）"""
    if os.path.isfile(path):
        return path

    # 支持的文件扩展名（按优先级排序）
    extensions = ["pdf", "docx", "doc", "txt", "md", "tex"]

    # 简单地遍历目录
    if os.path.isdir(path):
        try:
            for ext in extensions:
                # 手动检查每个可能的文件，而不使用glob
                potential_file = os.path.join(path, f"paper.{ext}")
                if os.path.exists(potential_file) and os.path.isfile(potential_file):
                    return potential_file

            # 如果没找到特定命名的文件，检查目录中的所有文件
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path):
                    file_ext = file.split('.')[-1].lower() if '.' in file else ""
                    if file_ext in extensions:
                        return file_path
        except Exception:
            pass  # 忽略任何错误

    return None