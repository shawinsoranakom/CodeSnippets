def _check_gpl3_header(self):
        header = '\n'.join(self.text.split('\n')[:20])
        if ('GNU General Public License' not in header or
                ('version 3' not in header and 'v3.0' not in header)):
            self.reporter.error(
                path=self.object_path,
                code='missing-gplv3-license',
                msg='GPLv3 license header not found in the first 20 lines of the module'
            )
        elif self._is_new_module():
            if len([line for line in header
                    if 'GNU General Public License' in line]) > 1:
                self.reporter.error(
                    path=self.object_path,
                    code='use-short-gplv3-license',
                    msg='Found old style GPLv3 license header: '
                        'https://docs.ansible.com/ansible-core/devel/dev_guide/developing_modules_documenting.html#copyright'
                )