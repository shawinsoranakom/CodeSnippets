def _write_description(self, label, ie_result, descfn):
        """ Write description and returns True = written, False = skip, None = error """
        if not self.params.get('writedescription'):
            return False
        elif not descfn:
            self.write_debug(f'Skipping writing {label} description')
            return False
        elif not self._ensure_dir_exists(descfn):
            return None
        elif not self.params.get('overwrites', True) and os.path.exists(descfn):
            self.to_screen(f'[info] {label.title()} description is already present')
        elif ie_result.get('description') is None:
            self.to_screen(f'[info] There\'s no {label} description to write')
            return False
        else:
            try:
                self.to_screen(f'[info] Writing {label} description to: {descfn}')
                with open(descfn, 'w', encoding='utf-8') as descfile:
                    descfile.write(ie_result['description'])
            except OSError:
                self.report_error(f'Cannot write {label} description file {descfn}')
                return None
        return True