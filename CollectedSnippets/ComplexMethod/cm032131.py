def _parse_work(self, work: Dict) -> PaperMetadata:
        """解析OpenAlex返回的数据"""
        # 获取作者信息
        raw_author_names = [
            authorship.get("raw_author_name", "")
            for authorship in work.get("authorships", [])
            if authorship
        ]
        # 处理作者名字格式
        authors = [
            self._reformat_name(author)
            for author in raw_author_names
        ]

        # 获取机构信息
        institutions = [
            inst.get("display_name", "")
            for authorship in work.get("authorships", [])
            for inst in authorship.get("institutions", [])
            if inst
        ]

        # 获取主要发表位置信息
        primary_location = work.get("primary_location") or {}
        source = primary_location.get("source") or {}
        venue = source.get("display_name")

        # 获取发表日期
        year = work.get("publication_year")

        return PaperMetadata(
            title=work.get("title", ""),
            authors=authors,
            institutions=institutions,
            abstract=work.get("abstract", ""),
            year=year,
            doi=work.get("doi"),
            url=work.get("doi"),  # OpenAlex 使用 DOI 作为 URL
            citations=work.get("cited_by_count"),
            venue=venue
        )