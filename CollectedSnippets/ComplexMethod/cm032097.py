def _extract_additional_metadata(self, elements, metadata: PaperMetadata) -> None:
        """提取其他元数据信息"""
        for element in elements[:30]:  # 只检查文档前部分
            element_text = str(element).strip()

            # 尝试匹配DOI
            doi_match = re.search(r'(doi|DOI):\s*(10\.\d{4,}\/[a-zA-Z0-9.-]+)', element_text)
            if doi_match and not metadata.doi:
                metadata.doi = doi_match.group(2)

            # 尝试匹配日期
            date_match = re.search(r'(published|received|accepted|submitted):\s*(\d{1,2}\s+[a-zA-Z]+\s+\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})', element_text, re.IGNORECASE)
            if date_match and not metadata.date:
                metadata.date = date_match.group(2)

            # 尝试匹配年份
            year_match = re.search(r'\b(19|20)\d{2}\b', element_text)
            if year_match and not metadata.year:
                metadata.year = year_match.group(0)

            # 尝试匹配期刊/会议名称
            journal_match = re.search(r'(journal|conference):\s*([^,;.]+)', element_text, re.IGNORECASE)
            if journal_match:
                if "journal" in journal_match.group(1).lower() and not metadata.journal:
                    metadata.journal = journal_match.group(2).strip()
                elif not metadata.conference:
                    metadata.conference = journal_match.group(2).strip()