def _parse_paper_data(self, paper) -> PaperMetadata:
        """解析论文数据"""
        # 获取DOI
        doi = None
        external_ids = paper.get('externalIds', {}) if isinstance(paper, dict) else paper.externalIds
        if external_ids:
            if isinstance(external_ids, dict):
                doi = external_ids.get('DOI')
                if not doi and 'ArXiv' in external_ids:
                    doi = f"10.48550/arXiv.{external_ids['ArXiv']}"
            else:
                doi = external_ids.DOI if hasattr(external_ids, 'DOI') else None
                if not doi and hasattr(external_ids, 'ArXiv'):
                    doi = f"10.48550/arXiv.{external_ids.ArXiv}"

        # 获取PDF URL
        pdf_url = None
        pdf_info = paper.get('openAccessPdf', {}) if isinstance(paper, dict) else paper.openAccessPdf
        if pdf_info:
            pdf_url = pdf_info.get('url') if isinstance(pdf_info, dict) else pdf_info.url

        # 获取发表场所详细信息
        venue_type = None
        venue_name = None
        venue_info = {}

        venue = paper.get('publicationVenue', {}) if isinstance(paper, dict) else paper.publicationVenue
        if venue:
            if isinstance(venue, dict):
                venue_name = venue.get('name')
                venue_type = venue.get('type')
                # 提取更多venue信息
                venue_info = {
                    'issn': venue.get('issn'),
                    'publisher': venue.get('publisher'),
                    'url': venue.get('url'),
                    'alternate_names': venue.get('alternate_names', [])
                }
            else:
                venue_name = venue.name if hasattr(venue, 'name') else None
                venue_type = venue.type if hasattr(venue, 'type') else None
                venue_info = {
                    'issn': getattr(venue, 'issn', None),
                    'publisher': getattr(venue, 'publisher', None),
                    'url': getattr(venue, 'url', None),
                    'alternate_names': getattr(venue, 'alternate_names', [])
                }

        # 获取标题
        title = paper.get('title', '') if isinstance(paper, dict) else getattr(paper, 'title', '')

        # 获取作者
        authors = paper.get('authors', []) if isinstance(paper, dict) else getattr(paper, 'authors', [])
        author_names = []
        for author in authors:
            if isinstance(author, dict):
                author_names.append(author.get('name', ''))
            else:
                author_names.append(author.name if hasattr(author, 'name') else str(author))

        # 获取摘要
        abstract = paper.get('abstract', '') if isinstance(paper, dict) else getattr(paper, 'abstract', '')

        # 获取年份
        year = paper.get('year') if isinstance(paper, dict) else getattr(paper, 'year', None)

        # 获取引用次数
        citations = paper.get('citationCount') if isinstance(paper, dict) else getattr(paper, 'citationCount', None)

        return PaperMetadata(
            title=title,
            authors=author_names,
            abstract=abstract,
            year=year,
            doi=doi,
            url=pdf_url or (f"https://doi.org/{doi}" if doi else None),
            citations=citations,
            venue=venue_name,
            institutions=[],
            venue_type=venue_type,
            venue_name=venue_name,
            venue_info=venue_info,
            source='semantic'  # 添加来源标记
        )