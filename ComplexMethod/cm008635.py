def _extract_video_id(data, lesson_id):
        if not data:
            return
        groups = try_get(data, lambda x: x['groups'], list) or []
        if not groups:
            return
        for group in groups:
            if not isinstance(group, dict):
                continue
            contents = try_get(data, lambda x: x['contents'], list) or []
            for content in contents:
                if not isinstance(content, dict):
                    continue
                ordinal = int_or_none(content.get('ordinal'))
                if ordinal != lesson_id:
                    continue
                video_id = content.get('identifier')
                if video_id:
                    return str(video_id)