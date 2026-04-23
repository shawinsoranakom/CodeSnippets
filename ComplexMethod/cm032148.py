def _normalize_journal_name(self, name: str) -> str:
        """标准化期刊名称

        Args:
            name: 原始期刊名称

        Returns:
            标准化后的期刊名称
        """
        if not name:
            return ""

        # 转换为小写
        name = name.lower()

        # 移除常见的前缀和后缀
        prefixes = ['the ', 'proceedings of ', 'journal of ']
        suffixes = [' journal', ' proceedings', ' magazine', ' review', ' letters']

        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):]

        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        # 移除特殊字符，保留字母、数字和空格
        name = ''.join(c for c in name if c.isalnum() or c.isspace())

        # 移除多余的空格
        name = ' '.join(name.split())

        return name