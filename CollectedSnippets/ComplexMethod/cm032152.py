def _parse_work(self, work: Dict) -> PaperMetadata:
        """解析Crossref返回的数据"""
        # 获取摘要 - 处理可能的不同格式
        abstract = ""
        if isinstance(work.get("abstract"), str):
            abstract = work.get("abstract", "")
        elif isinstance(work.get("abstract"), dict):
            abstract = work.get("abstract", {}).get("value", "")

        if not abstract:
            print(f"警告: 论文 '{work.get('title', [''])[0]}' 没有可用的摘要")

        # 获取机构信息
        institutions = []
        for author in work.get("author", []):
            if "affiliation" in author:
                for affiliation in author["affiliation"]:
                    if "name" in affiliation and affiliation["name"] not in institutions:
                        institutions.append(affiliation["name"])

        # 获取venue信息
        venue_name = work.get("container-title", [None])[0]
        venue_type = work.get("type", "unknown")  # 文献类型
        venue_info = {
            "publisher": work.get("publisher"),
            "issn": work.get("ISSN", []),
            "isbn": work.get("ISBN", []),
            "issue": work.get("issue"),
            "volume": work.get("volume"),
            "page": work.get("page")
        }

        return PaperMetadata(
            title=work.get("title", [None])[0] or "",
            authors=[
                author.get("given", "") + " " + author.get("family", "")
                for author in work.get("author", [])
            ],
            institutions=institutions,  # 添加机构信息
            abstract=abstract,
            year=work.get("published-print", {}).get("date-parts", [[None]])[0][0],
            doi=work.get("DOI"),
            url=f"https://doi.org/{work.get('DOI')}" if work.get("DOI") else None,
            citations=work.get("is-referenced-by-count"),
            venue=venue_name,
            venue_type=venue_type,  # 添加venue类型
            venue_name=venue_name,  # 添加venue名称
            venue_info=venue_info,  # 添加venue详细信息
            source='crossref'  # 添加来源标记
        )