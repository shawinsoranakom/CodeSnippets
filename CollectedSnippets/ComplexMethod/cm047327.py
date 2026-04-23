def run_rtlcss(self, source):
        rtlcss = 'rtlcss'
        if os.name == 'nt':
            try:
                rtlcss = misc.find_in_path('rtlcss.cmd')
            except IOError:
                rtlcss = 'rtlcss'

        cmd = [rtlcss, '-c', file_path("base/data/rtlcss.json"), '-']

        try:
            rtlcss = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf-8')
        except Exception:

            # Check the presence of rtlcss, if rtlcss not available then we should return normal less file
            try:
                process = Popen(
                    ['rtlcss', '--version'], stdout=PIPE, stderr=PIPE
                )
            except (OSError, IOError):
                _logger.warning('You need https://rtlcss.com/ to convert css file to right to left compatiblity. Use: npm install -g rtlcss')
                return source

            msg = "Could not execute command %r" % cmd[0]
            _logger.error(msg)
            self.css_errors.append(msg)
            return ''

        out, err = rtlcss.communicate(input=source)
        if rtlcss.returncode or (source and not out):
            if rtlcss.returncode:
                error = self.get_rtlcss_error(err or f"Process exited with return code {rtlcss.returncode}", source=source)
            else:
                error = "rtlcss: error processing payload\n"
            _logger.warning("%s", error)
            self.css_errors.append(error)
            return ''
        return out.strip()