def _get_entry_type(self, paper: PaperMetadata) -> str:
        """确定BibTeX条目类型"""
        if hasattr(paper, 'venue_type') and paper.venue_type:
            venue_type = paper.venue_type.lower()
            if venue_type == 'conference':
                return 'inproceedings'
            elif venue_type == 'preprint':
                return 'unpublished'
            elif venue_type == 'journal':
                return 'article'
            elif venue_type == 'book':
                return 'book'
            elif venue_type == 'thesis':
                return 'phdthesis'
        return 'article'