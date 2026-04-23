def _add_result(self, test, capture=False, **args):
        if not self.USE_XML:
            return
        e = self.__e
        self.__e = None
        if e is None:
            return
        ET = self.__ET

        e.set('name', args.pop('name', self.__getId(test)))
        e.set('status', args.pop('status', 'run'))
        e.set('result', args.pop('result', 'completed'))
        if self.__start_time:
            e.set('time', f'{time.perf_counter() - self.__start_time:0.6f}')

        if capture:
            if self._stdout_buffer is not None:
                stdout = self._stdout_buffer.getvalue().rstrip()
                ET.SubElement(e, 'system-out').text = sanitize_xml(stdout)
            if self._stderr_buffer is not None:
                stderr = self._stderr_buffer.getvalue().rstrip()
                ET.SubElement(e, 'system-err').text = sanitize_xml(stderr)

        for k, v in args.items():
            if not k or not v:
                continue

            e2 = ET.SubElement(e, k)
            if hasattr(v, 'items'):
                for k2, v2 in v.items():
                    if k2:
                        e2.set(k2, sanitize_xml(str(v2)))
                    else:
                        e2.text = sanitize_xml(str(v2))
            else:
                e2.text = sanitize_xml(str(v))