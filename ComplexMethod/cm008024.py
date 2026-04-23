def __forced_printings(self, info_dict, filename=None, incomplete=True):
        if (self.params.get('forcejson')
                or self.params['forceprint'].get('video')
                or self.params['print_to_file'].get('video')):
            self.post_extract(info_dict)
        if filename:
            info_dict['filename'] = filename
        info_copy = self._forceprint('video', info_dict)

        def print_field(field, actual_field=None, optional=False):
            if actual_field is None:
                actual_field = field
            if self.params.get(f'force{field}') and (
                    info_copy.get(field) is not None or (not optional and not incomplete)):
                self.to_stdout(info_copy[actual_field])

        print_field('title')
        print_field('id')
        print_field('url', 'urls')
        print_field('thumbnail', optional=True)
        print_field('description', optional=True)
        print_field('filename')
        if self.params.get('forceduration') and info_copy.get('duration') is not None:
            self.to_stdout(formatSeconds(info_copy['duration']))
        print_field('format')

        if self.params.get('forcejson'):
            self.to_stdout(json.dumps(self.sanitize_info(info_dict)))