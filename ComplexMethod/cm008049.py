def simplified_codec(f, field):
            assert field in ('acodec', 'vcodec')
            codec = f.get(field)
            if not codec:
                return 'unknown'
            elif codec != 'none':
                return '.'.join(codec.split('.')[:4])

            if field == 'vcodec' and f.get('acodec') == 'none':
                return 'images'
            elif field == 'acodec' and f.get('vcodec') == 'none':
                return ''
            return self._format_out('audio only' if field == 'vcodec' else 'video only',
                                    self.Styles.SUPPRESS)