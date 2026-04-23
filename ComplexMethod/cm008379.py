def _search_nextjs_v13_data(self, webpage, video_id, fatal=True):
        """Parses Next.js app router flight data that was introduced in Next.js v13"""
        nextjs_data = {}
        if not fatal and not isinstance(webpage, str):
            return nextjs_data

        def flatten(flight_data):
            if not isinstance(flight_data, list):
                return
            if len(flight_data) == 4 and flight_data[0] == '$':
                _, name, _, data = flight_data
                if not isinstance(data, dict):
                    return
                children = data.pop('children', None)
                if data and isinstance(name, str) and re.fullmatch(r'\$L[0-9a-f]+', name):
                    # It is useful hydration JSON data
                    nextjs_data[name[2:]] = data
                flatten(children)
                return
            for f in flight_data:
                flatten(f)

        flight_text = ''
        # The pattern for the surrounding JS/tag should be strict as it's a hardcoded string in the next.js source
        # Ref: https://github.com/vercel/next.js/blob/5a4a08fdc/packages/next/src/server/app-render/use-flight-response.tsx#L189
        for flight_segment in re.findall(r'<script\b[^>]*>self\.__next_f\.push\((\[.+?\])\)</script>', webpage):
            segment = self._parse_json(flight_segment, video_id, fatal=fatal, errnote=None if fatal else False)
            # Some earlier versions of next.js "optimized" away this array structure; this is unsupported
            # Ref: https://github.com/vercel/next.js/commit/0123a9d5c9a9a77a86f135b7ae30b46ca986d761
            if not isinstance(segment, list) or len(segment) != 2:
                self.write_debug(
                    f'{video_id}: Unsupported next.js flight data structure detected', only_once=True)
                continue
            # Only use the relevant payload type (1 == data)
            # Ref: https://github.com/vercel/next.js/blob/5a4a08fdc/packages/next/src/server/app-render/use-flight-response.tsx#L11-L14
            payload_type, chunk = segment
            if payload_type == 1:
                flight_text += chunk

        for f in flight_text.splitlines():
            prefix, _, body = f.lstrip().partition(':')
            if not re.fullmatch(r'[0-9a-f]+', prefix):
                continue
            # The body still isn't guaranteed to be valid JSON, so parsing should always be non-fatal
            if body.startswith('[') and body.endswith(']'):
                flatten(self._parse_json(body, video_id, fatal=False, errnote=False))
            elif body.startswith('{') and body.endswith('}'):
                data = self._parse_json(body, video_id, fatal=False, errnote=False)
                if data is not None:
                    nextjs_data[prefix] = data

        return nextjs_data