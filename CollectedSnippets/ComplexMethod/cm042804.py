def ffmpeg_concat_av(files, output, ext):
    print('Merging video parts... ', end="", flush=True)
    params = [FFMPEG] + LOGLEVEL
    for file in files:
        if os.path.isfile(file): params.extend(['-i', file])
    params.extend(['-c', 'copy'])
    params.extend(['--', output])
    if subprocess.call(params, stdin=STDIN):
        print('Merging without re-encode failed.\nTry again re-encoding audio... ', end="", flush=True)
        try: os.remove(output)
        except FileNotFoundError: pass
        params = [FFMPEG] + LOGLEVEL
        for file in files:
            if os.path.isfile(file): params.extend(['-i', file])
        params.extend(['-c:v', 'copy'])
        if ext == 'mp4':
            params.extend(['-c:a', 'aac'])
            params.extend(['-strict', 'experimental'])
        elif ext == 'webm':
            params.extend(['-c:a', 'opus'])
        params.extend(['--', output])
        return subprocess.call(params, stdin=STDIN)
    else:
        return 0