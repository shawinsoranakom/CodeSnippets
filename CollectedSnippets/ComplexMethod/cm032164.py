def _generate_cite_key(self, paper: PaperMetadata) -> str:
        """生成引用键
        格式: 第一作者姓氏_年份_第一个实词
        """
        # 获取第一作者姓氏
        first_author = ""
        if paper.authors and len(paper.authors) > 0:
            first_author = paper.authors[0].split()[-1].lower()

        # 获取年份
        year = str(paper.year) if paper.year else "0000"

        # 从标题中获取第一个实词
        title_word = ""
        if paper.title:
            # 移除特殊字符，分割成单词
            words = re.findall(r'\w+', paper.title.lower())
            # 过滤掉常见的停用词
            stop_words = {'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            for word in words:
                if word not in stop_words and len(word) > 2:
                    title_word = word
                    break

        # 组合cite key
        cite_key = f"{first_author}{year}{title_word}"

        # 确保cite key只包含合法字符
        cite_key = re.sub(r'[^a-z0-9]', '', cite_key.lower())

        return cite_key