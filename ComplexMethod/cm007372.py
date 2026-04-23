def simplified_codec(f, field):
            assert field in ('acodec', 'vcodec')
            codec = f.get(field)
            return (
                'unknown' if not codec
                else '.'.join(codec.split('.')[:4]) if codec != 'none'
                else 'images' if field == 'vcodec' and f.get('acodec') == 'none'
                else None if field == 'acodec' and f.get('vcodec') == 'none'
                else 'audio only' if field == 'vcodec'
                else 'video only')