def _real_extract(self, url, html=None):
        # exceptionally, id may be None
        m_dict = self._match_valid_url(url).groupdict()
        pl_id, page_type, sort = (m_dict.get(k) for k in ('id', 'type', 'sort'))

        qs = parse_qs(url)
        for q, v in qs.items():
            if v:
                qs[q] = v[-1]
            else:
                del qs[q]

        base_id = pl_id or 'YouPorn'
        title = self._get_title_from_slug(base_id)
        if page_type:
            title = '%s %s' % (page_type.capitalize(), title)
        base_id = [base_id.lower()]
        if sort is None:
            title += ' videos'
        else:
            title = '%s videos by %s' % (title, re.sub(r'[_-]', ' ', sort))
            base_id.append(sort)
        if qs:
            ps = ['%s=%s' % item for item in sorted(qs.items())]
            title += ' (%s)' % ','.join(ps)
            base_id.extend(ps)
        pl_id = '/'.join(base_id)

        return self.playlist_result(
            self._entries(url, pl_id, html=html,
                          page_num=int_or_none(qs.get('page'))),
            playlist_id=pl_id, playlist_title=title)