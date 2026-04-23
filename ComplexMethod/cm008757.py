def _mark_chapters_to_remove(self, chapters, sponsor_chapters):
        if self._remove_chapters_patterns:
            warn_no_chapter_to_remove = True
            if not chapters:
                self.to_screen('Chapter information is unavailable')
                warn_no_chapter_to_remove = False
            for c in chapters:
                if any(regex.search(c['title']) for regex in self._remove_chapters_patterns):
                    c['remove'] = True
                    warn_no_chapter_to_remove = False
            if warn_no_chapter_to_remove:
                self.to_screen('There are no chapters matching the regex')

        if self._remove_sponsor_segments:
            warn_no_chapter_to_remove = True
            if not sponsor_chapters:
                self.to_screen('SponsorBlock information is unavailable')
                warn_no_chapter_to_remove = False
            for c in sponsor_chapters:
                if c['category'] in self._remove_sponsor_segments:
                    c['remove'] = True
                    warn_no_chapter_to_remove = False
            if warn_no_chapter_to_remove:
                self.to_screen('There are no matching SponsorBlock chapters')

        sponsor_chapters.extend({
            'start_time': start,
            'end_time': end,
            'category': 'manually_removed',
            '_categories': [('manually_removed', start, end, 'Manually removed')],
            'remove': True,
        } for start, end in self._ranges_to_remove)

        return chapters, sponsor_chapters