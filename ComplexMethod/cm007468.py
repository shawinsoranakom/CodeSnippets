def _entries(self, username, channel_id):
        created_before = 0
        for page_num in itertools.count(1):
            if created_before is None:
                break
            info = self._download_json(
                '%s/moment/profile/channelId=%s/createdBefore=%d/records=20'
                % (CDN_API_BASE, channel_id, created_before), username,
                note='Downloading moments page %d' % page_num)
            items = info.get('items')
            if not items or not isinstance(items, list):
                break
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_type = item.get('type')
                if item_type == 'moment':
                    entry = _extract_moment(item, fatal=False)
                    if entry:
                        yield entry
                elif item_type == 'collection':
                    moments = item.get('momentsIds')
                    if isinstance(moments, list):
                        for moment_id in moments:
                            m = self._download_json(
                                MOMENT_URL_FORMAT % moment_id, username,
                                note='Downloading %s moment JSON' % moment_id,
                                fatal=False)
                            if m and isinstance(m, dict) and m.get('item'):
                                entry = _extract_moment(m['item'])
                                if entry:
                                    yield entry
                created_before = int_or_none(item.get('created'))