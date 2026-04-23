def prepare_filename(self, info_dict, dir_type='', *, outtmpl=None, warn=False):
        """Generate the output filename"""
        if outtmpl:
            assert not dir_type, 'outtmpl and dir_type are mutually exclusive'
            dir_type = None
        filename = self._prepare_filename(info_dict, tmpl_type=dir_type, outtmpl=outtmpl)
        if not filename and dir_type not in ('', 'temp'):
            return ''

        if warn:
            if not self.params.get('paths'):
                pass
            elif filename == '-':
                self.report_warning('--paths is ignored when an outputting to stdout', only_once=True)
            elif os.path.isabs(filename):
                self.report_warning('--paths is ignored since an absolute path is given in output template', only_once=True)
        if filename == '-' or not filename:
            return filename

        return self.get_output_path(dir_type, filename)