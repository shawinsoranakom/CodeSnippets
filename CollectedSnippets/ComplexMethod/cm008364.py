def _extract_mhtml_formats(base_url, timestamps):
        image_frags = {}
        for timestamp in timestamps or []:
            duration = timestamp.get('Duration')
            obj_id, obj_sn = timestamp.get('ObjectIdentifier'), timestamp.get('ObjectSequenceNumber')
            if timestamp.get('EventTargetType') == 'PowerPoint' and obj_id is not None and obj_sn is not None:
                image_frags.setdefault('slides', []).append({
                    'url': base_url + f'/Pages/Viewer/Image.aspx?id={obj_id}&number={obj_sn}',
                    'duration': duration,
                })

            obj_pid, session_id, abs_time = timestamp.get('ObjectPublicIdentifier'), timestamp.get('SessionID'), timestamp.get('AbsoluteTime')
            if None not in (obj_pid, session_id, abs_time):
                image_frags.setdefault('chapter', []).append({
                    'url': base_url + f'/Pages/Viewer/Thumb.aspx?eventTargetPID={obj_pid}&sessionPID={session_id}&number={obj_sn}&isPrimary=false&absoluteTime={abs_time}',
                    'duration': duration,
                })
        for name, fragments in image_frags.items():
            yield {
                'format_id': name,
                'ext': 'mhtml',
                'protocol': 'mhtml',
                'acodec': 'none',
                'vcodec': 'none',
                'url': 'about:invalid',
                'fragments': fragments,
            }