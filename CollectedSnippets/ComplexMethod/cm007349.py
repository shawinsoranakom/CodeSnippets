def _match_entry(self, info_dict, incomplete):
        """ Returns None iff the file should be downloaded """

        video_title = info_dict.get('title', info_dict.get('id', 'video'))
        if 'title' in info_dict:
            # This can happen when we're just evaluating the playlist
            title = info_dict['title']
            matchtitle = self.params.get('matchtitle', False)
            if matchtitle:
                if not re.search(matchtitle, title, re.IGNORECASE):
                    return '"' + title + '" title did not match pattern "' + matchtitle + '"'
            rejecttitle = self.params.get('rejecttitle', False)
            if rejecttitle:
                if re.search(rejecttitle, title, re.IGNORECASE):
                    return '"' + title + '" title matched reject pattern "' + rejecttitle + '"'
        date = info_dict.get('upload_date')
        if date is not None:
            dateRange = self.params.get('daterange', DateRange())
            if date not in dateRange:
                return '%s upload date is not in range %s' % (date_from_str(date).isoformat(), dateRange)
        view_count = info_dict.get('view_count')
        if view_count is not None:
            min_views = self.params.get('min_views')
            if min_views is not None and view_count < min_views:
                return 'Skipping %s, because it has not reached minimum view count (%d/%d)' % (video_title, view_count, min_views)
            max_views = self.params.get('max_views')
            if max_views is not None and view_count > max_views:
                return 'Skipping %s, because it has exceeded the maximum view count (%d/%d)' % (video_title, view_count, max_views)
        if age_restricted(info_dict.get('age_limit'), self.params.get('age_limit')):
            return 'Skipping "%s" because it is age restricted' % video_title
        if self.in_download_archive(info_dict):
            return '%s has already been recorded in archive' % video_title

        if not incomplete:
            match_filter = self.params.get('match_filter')
            if match_filter is not None:
                ret = match_filter(info_dict)
                if ret is not None:
                    return ret

        return None