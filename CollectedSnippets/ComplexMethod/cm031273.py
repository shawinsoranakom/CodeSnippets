def __repr__(self):
        info = [self.__class__.__name__]
        if self._closed:
            info.append('closed')
        if self._pid is not None:
            info.append(f'pid={self._pid}')
        if self._returncode is not None:
            info.append(f'returncode={self._returncode}')
        elif self._pid is not None:
            info.append('running')
        else:
            info.append('not started')

        stdin = self._pipes.get(0)
        if stdin is not None:
            info.append(f'stdin={stdin.pipe}')

        stdout = self._pipes.get(1)
        stderr = self._pipes.get(2)
        if stdout is not None and stderr is stdout:
            info.append(f'stdout=stderr={stdout.pipe}')
        else:
            if stdout is not None:
                info.append(f'stdout={stdout.pipe}')
            if stderr is not None:
                info.append(f'stderr={stderr.pipe}')

        return '<{}>'.format(' '.join(info))