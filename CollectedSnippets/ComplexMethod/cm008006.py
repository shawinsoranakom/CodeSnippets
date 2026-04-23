def _prepare_filename(self, info_dict, *, outtmpl=None, tmpl_type=None):
        assert None in (outtmpl, tmpl_type), 'outtmpl and tmpl_type are mutually exclusive'
        if outtmpl is None:
            outtmpl = self.params['outtmpl'].get(tmpl_type or 'default', self.params['outtmpl']['default'])
        try:
            outtmpl = self._outtmpl_expandpath(outtmpl)
            filename = self.evaluate_outtmpl(outtmpl, info_dict, True)
            if not filename:
                return None

            if tmpl_type in ('', 'temp'):
                final_ext, ext = self.params.get('final_ext'), info_dict.get('ext')
                if final_ext and ext and final_ext != ext and filename.endswith(f'.{final_ext}'):
                    filename = replace_extension(filename, ext, final_ext)
            elif tmpl_type:
                force_ext = OUTTMPL_TYPES[tmpl_type]
                if force_ext:
                    filename = replace_extension(filename, force_ext, info_dict.get('ext'))

            # https://github.com/blackjack4494/youtube-dlc/issues/85
            trim_file_name = self.params.get('trim_file_name', False)
            if trim_file_name:
                no_ext, *ext = filename.rsplit('.', 2)
                filename = join_nonempty(no_ext[:trim_file_name], *ext, delim='.')

            return filename
        except ValueError as err:
            self.report_error('Error in output template: ' + str(err) + ' (encoding: ' + repr(preferredencoding()) + ')')
            return None