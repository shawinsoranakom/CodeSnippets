def buildPythonDocs():
    # This stores the documentation as Resources/English.lproj/Documentation
    # inside the framework. pydoc and IDLE will pick it up there.
    print("Install python documentation")
    rootDir = os.path.join(WORKDIR, '_root')
    buildDir = os.path.join('../../Doc')
    docdir = os.path.join(rootDir, 'pydocs')
    curDir = os.getcwd()
    os.chdir(buildDir)
    runCommand('make clean')

    # Search third-party source directory for a pre-built version of the docs.
    #   Use the naming convention of the docs.python.org html downloads:
    #       python-3.9.0b1-docs-html.tar.bz2
    doctarfiles = [ f for f in os.listdir(DEPSRC)
        if f.startswith('python-'+getFullVersion())
        if f.endswith('-docs-html.tar.bz2') ]
    if doctarfiles:
        doctarfile = doctarfiles[0]
        if not os.path.exists('build'):
            os.mkdir('build')
        # if build directory existed, it was emptied by make clean, above
        os.chdir('build')
        # Extract the first archive found for this version into build
        runCommand('tar xjf %s'%shellQuote(os.path.join(DEPSRC, doctarfile)))
        # see if tar extracted a directory ending in -docs-html
        archivefiles = [ f for f in os.listdir('.')
            if f.endswith('-docs-html')
            if os.path.isdir(f) ]
        if archivefiles:
            archivefile = archivefiles[0]
            # make it our 'Docs/build/html' directory
            print(' -- using pre-built python documentation from %s'%archivefile)
            os.rename(archivefile, 'html')
        os.chdir(buildDir)

    htmlDir = os.path.join('build', 'html')
    if not os.path.exists(htmlDir):
        # Create virtual environment for docs builds with blurb and sphinx
        runCommand('make venv')
        runCommand('make html PYTHON=venv/bin/python')
    os.rename(htmlDir, docdir)
    os.chdir(curDir)