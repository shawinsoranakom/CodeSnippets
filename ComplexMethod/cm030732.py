def test_select(self):
        code = textwrap.dedent('''
            import time
            for i in range(10):
                print("testing...", flush=True)
                time.sleep(0.050)
        ''')
        cmd = [sys.executable, '-I', '-c', code]
        with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
            pipe = proc.stdout
            for timeout in (0, 1, 2, 4, 8, 16) + (None,)*10:
                if support.verbose:
                    print(f'timeout = {timeout}')
                rfd, wfd, xfd = select.select([pipe], [], [], timeout)
                self.assertEqual(wfd, [])
                self.assertEqual(xfd, [])
                if not rfd:
                    continue
                if rfd == [pipe]:
                    line = pipe.readline()
                    if support.verbose:
                        print(repr(line))
                    if not line:
                        if support.verbose:
                            print('EOF')
                        break
                    continue
                self.fail('Unexpected return values from select():',
                          rfd, wfd, xfd)