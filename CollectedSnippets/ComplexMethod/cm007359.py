def __forced_printings(self, info_dict, filename, incomplete):
        def print_mandatory(field):
            if (self.params.get('force%s' % field, False)
                    and (not incomplete or info_dict.get(field) is not None)):
                self.to_stdout(info_dict[field])

        def print_optional(field):
            if (self.params.get('force%s' % field, False)
                    and info_dict.get(field) is not None):
                self.to_stdout(info_dict[field])

        print_mandatory('title')
        print_mandatory('id')
        if self.params.get('forceurl', False) and not incomplete:
            if info_dict.get('requested_formats') is not None:
                for f in info_dict['requested_formats']:
                    self.to_stdout(f['url'] + f.get('play_path', ''))
            else:
                # For RTMP URLs, also include the playpath
                self.to_stdout(info_dict['url'] + info_dict.get('play_path', ''))
        print_optional('thumbnail')
        print_optional('description')
        if self.params.get('forcefilename', False) and filename is not None:
            self.to_stdout(filename)
        if self.params.get('forceduration', False) and info_dict.get('duration') is not None:
            self.to_stdout(formatSeconds(info_dict['duration']))
        print_mandatory('format')
        if self.params.get('forcejson', False):
            self.to_stdout(json.dumps(self.sanitize_info(info_dict)))