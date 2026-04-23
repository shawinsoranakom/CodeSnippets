def create_repo():
    pkgs = []
    for spec in SPECS:
        pkg = SimpleRpmBuild(spec.name, spec.version, spec.release, spec.arch or ['noarch'])
        pkg.epoch = spec.epoch

        for requires in spec.requires or []:
            pkg.add_requires(requires)

        for recommend in spec.recommends or []:
            pkg.add_recommends(recommend)

        for provide in spec.provides or []:
            pkg.add_provides(provide)

        if spec.file:
            pkg.add_installed_file(
                "/" + spec.file,
                GeneratedSourceFile(
                    spec.file, make_gif()
                )
            )

        if spec.pre:
            pkg.add_pre(spec.pre)

        if spec.binary:
            pkg.add_simple_compilation(installPath=spec.binary)

        pkgs.append(pkg)

    repo = YumRepoBuild(pkgs)
    repo.make('noarch', 'i686', 'x86_64', expectedArch)

    for pkg in pkgs:
        pkg.clean()

    return repo.repoDir