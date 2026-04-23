def _real_extract(self, url, html=None):
        m_dict = self._match_valid_url(url).groupdict()
        pl_id, page_type, sort = (m_dict.get(k) for k in ('id', 'type', 'sort'))
        qs = {k: v[-1] for k, v in parse_qs(url).items() if v}

        base_id = pl_id or 'YouPorn'
        title = self._get_title_from_slug(base_id)
        if page_type:
            title = f'{page_type.capitalize()} {title}'
        base_id = [base_id.lower()]
        if sort is None:
            title += ' videos'
        else:
            title = f'{title} videos by {re.sub(r"[_-]", " ", sort)}'
            base_id.append(sort)
        if qs:
            filters = list(map('='.join, sorted(qs.items())))
            title += f' ({",".join(filters)})'
            base_id.extend(filters)
        pl_id = '/'.join(base_id)

        return self.playlist_result(
            self._entries(url, pl_id, html=html, page_num=int_or_none(qs.get('page'))),
            playlist_id=pl_id, playlist_title=title)