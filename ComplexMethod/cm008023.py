def _forceprint(self, key, info_dict):
        if info_dict is None:
            return
        info_copy = info_dict.copy()
        info_copy.setdefault('filename', self.prepare_filename(info_dict))
        if info_dict.get('requested_formats') is not None:
            # For RTMP URLs, also include the playpath
            info_copy['urls'] = '\n'.join(f['url'] + f.get('play_path', '') for f in info_dict['requested_formats'])
        elif info_dict.get('url'):
            info_copy['urls'] = info_dict['url'] + info_dict.get('play_path', '')
        info_copy['formats_table'] = self.render_formats_table(info_dict)
        info_copy['thumbnails_table'] = self.render_thumbnails_table(info_dict)
        info_copy['subtitles_table'] = self.render_subtitles_table(info_dict.get('id'), info_dict.get('subtitles'))
        info_copy['automatic_captions_table'] = self.render_subtitles_table(info_dict.get('id'), info_dict.get('automatic_captions'))

        def format_tmpl(tmpl):
            mobj = re.fullmatch(r'([\w.:,]|-\d|(?P<dict>{([\w.:,]|-\d)+}))+=?', tmpl)
            if not mobj:
                return tmpl

            fmt = '%({})s'
            if tmpl.startswith('{'):
                tmpl, fmt = f'.{tmpl}', '%({})j'
            if tmpl.endswith('='):
                tmpl, fmt = tmpl[:-1], '{0} = %({0})#j'
            return '\n'.join(map(fmt.format, [tmpl] if mobj.group('dict') else tmpl.split(',')))

        for tmpl in self.params['forceprint'].get(key, []):
            self.to_stdout(self.evaluate_outtmpl(format_tmpl(tmpl), info_copy))

        for tmpl, file_tmpl in self.params['print_to_file'].get(key, []):
            filename = self.prepare_filename(info_dict, outtmpl=file_tmpl)
            tmpl = format_tmpl(tmpl)
            self.to_screen(f'[info] Writing {tmpl!r} to: {filename}')
            if self._ensure_dir_exists(filename):
                with open(filename, 'a', encoding='utf-8', newline='') as f:
                    f.write(self.evaluate_outtmpl(tmpl, info_copy) + os.linesep)

        return info_copy