def plain(self, warnings=False, output='-'):
        """Print out the test results in plain format

        output is ignored here for now
        """
        ret = []

        for path, report in Reporter._filter_out_ok(self.files).items():
            traces = report['traces'][:]
            if warnings and report['warnings']:
                traces.extend(report['warning_traces'])

            for trace in traces:
                print('TRACE:')
                print('\n    '.join(('    %s' % trace).splitlines()))
            for error in report['errors']:
                error['path'] = path
                print('%(path)s:%(line)d:%(column)d: E%(code)s %(msg)s' % error)
                ret.append(1)
            if warnings:
                for warning in report['warnings']:
                    warning['path'] = path
                    print('%(path)s:%(line)d:%(column)d: W%(code)s %(msg)s' % warning)

        return 3 if ret else 0