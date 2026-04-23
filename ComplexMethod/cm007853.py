def yield_items():
            for item in traverse_obj(data, (
                    'content', 'items', lambda _, v: any(k in v['target']['params'] for k in self._ID_NAMES))):
                if item_id is None or item_id == txt_or_none(item.get('id')):
                    target = item['target']
                    typed_item_id = self._get_item_id(target['params'])
                    station = target['params'].get('station')
                    item_type = target.get('type')
                    if typed_item_id and (station or item_type):
                        yield station, typed_item_id, item_type
                    if item_id is not None:
                        break
            else:
                if item_id is not None:
                    raise ExtractorError('Item not found in collection',
                                         video_id=coll_id, expected=True)