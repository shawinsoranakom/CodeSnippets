def launch_player(player, urls):
    import subprocess
    import shlex
    urls = list(urls)
    for url in urls.copy():
        if type(url) is list:
            urls.extend(url)
    urls = [url for url in urls if type(url) is str]
    assert urls
    if (sys.version_info >= (3, 3)):
        import shutil
        exefile=shlex.split(player)[0]
        if shutil.which(exefile) is not None:
            subprocess.call(shlex.split(player) + urls)
        else:
            log.wtf('[Failed] Cannot find player "%s"' % exefile)
    else:
        subprocess.call(shlex.split(player) + urls)