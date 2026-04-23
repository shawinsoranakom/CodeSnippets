def _collect_files(self, path: str) -> List[FileInfo]:
        """收集文件信息

        Args:
            path: 目标路径

        Returns:
            List[FileInfo]: 有效文件信息列表
        """
        files = []
        total_size = 0

        # 处理单个文件的情况
        if os.path.isfile(path):
            if self._is_valid_file(path):
                file_info = self._create_file_info(os.DirEntry(os.path.dirname(path)), os.path.dirname(path))
                if file_info:
                    return [file_info]
            return []

        # 处理目录的情况
        try:
            # 使用os.walk来递归遍历目录
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    if len(files) >= self.MAX_FILES:
                        self.failed_files.append((filename, f"超出最大文件数限制({self.MAX_FILES})"))
                        continue

                    file_path = os.path.join(root, filename)

                    if not self._is_valid_file(file_path):
                        continue

                    try:
                        stats = os.stat(file_path)
                        file_size = stats.st_size / (1024 * 1024)  # 转换为MB

                        if file_size * 1024 * 1024 > self.MAX_FILE_SIZE:
                            self.failed_files.append((file_path,
                                f"文件过大（{file_size:.2f}MB > {self.MAX_FILE_SIZE / (1024 * 1024)}MB）"))
                            continue

                        if total_size + file_size * 1024 * 1024 > self.MAX_TOTAL_SIZE:
                            self.failed_files.append((file_path, "超出总大小限制"))
                            continue

                        file_info = FileInfo(
                            path=file_path,
                            rel_path=os.path.relpath(file_path, path),
                            size=file_size,
                            extension=os.path.splitext(file_path)[1].lower(),
                            last_modified=time.strftime('%Y-%m-%d %H:%M:%S',
                                                      time.localtime(stats.st_mtime))
                        )

                        total_size += file_size * 1024 * 1024
                        files.append(file_info)

                    except Exception as e:
                        self.failed_files.append((file_path, f"处理文件失败: {str(e)}"))
                        continue

        except Exception as e:
            self.failed_files.append(("目录扫描", f"扫描失败: {str(e)}"))
            return []

        return sorted(files, key=lambda x: x.rel_path)