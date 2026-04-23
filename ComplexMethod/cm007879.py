def run_rtmpdump(args):
            start = time.time()
            resume_percent = None
            resume_downloaded_data_len = None
            proc = subprocess.Popen(args, stderr=subprocess.PIPE)
            cursor_in_new_line = True
            proc_stderr_closed = False
            try:
                while not proc_stderr_closed:
                    # read line from stderr
                    line = ''
                    while True:
                        char = proc.stderr.read(1)
                        if not char:
                            proc_stderr_closed = True
                            break
                        if char in [b'\r', b'\n']:
                            break
                        line += char.decode('ascii', 'replace')
                    if not line:
                        # proc_stderr_closed is True
                        continue
                    mobj = re.search(r'([0-9]+\.[0-9]{3}) kB / [0-9]+\.[0-9]{2} sec \(([0-9]{1,2}\.[0-9])%\)', line)
                    if mobj:
                        downloaded_data_len = int(float(mobj.group(1)) * 1024)
                        percent = float(mobj.group(2))
                        if not resume_percent:
                            resume_percent = percent
                            resume_downloaded_data_len = downloaded_data_len
                        time_now = time.time()
                        eta = self.calc_eta(start, time_now, 100 - resume_percent, percent - resume_percent)
                        speed = self.calc_speed(start, time_now, downloaded_data_len - resume_downloaded_data_len)
                        data_len = None
                        if percent > 0:
                            data_len = int(downloaded_data_len * 100 / percent)
                        self._hook_progress({
                            'status': 'downloading',
                            'downloaded_bytes': downloaded_data_len,
                            'total_bytes_estimate': data_len,
                            'tmpfilename': tmpfilename,
                            'filename': filename,
                            'eta': eta,
                            'elapsed': time_now - start,
                            'speed': speed,
                        })
                        cursor_in_new_line = False
                    else:
                        # no percent for live streams
                        mobj = re.search(r'([0-9]+\.[0-9]{3}) kB / [0-9]+\.[0-9]{2} sec', line)
                        if mobj:
                            downloaded_data_len = int(float(mobj.group(1)) * 1024)
                            time_now = time.time()
                            speed = self.calc_speed(start, time_now, downloaded_data_len)
                            self._hook_progress({
                                'downloaded_bytes': downloaded_data_len,
                                'tmpfilename': tmpfilename,
                                'filename': filename,
                                'status': 'downloading',
                                'elapsed': time_now - start,
                                'speed': speed,
                            })
                            cursor_in_new_line = False
                        elif self.params.get('verbose', False):
                            if not cursor_in_new_line:
                                self.to_screen('')
                            cursor_in_new_line = True
                            self.to_screen('[rtmpdump] ' + line)
                if not cursor_in_new_line:
                    self.to_screen('')
                return proc.wait()
            except BaseException:  # Including KeyboardInterrupt
                proc.kill()
                proc.wait()
                raise