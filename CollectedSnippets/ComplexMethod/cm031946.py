def preprocess (self,
                    source,
                    output_file=None,
                    macros=None,
                    include_dirs=None,
                    extra_preargs=None,
                    extra_postargs=None):

        (_, macros, include_dirs) = \
            self._fix_compile_args(None, macros, include_dirs)
        pp_opts = gen_preprocess_options(macros, include_dirs)
        pp_args = ['cpp32.exe'] + pp_opts
        if output_file is not None:
            pp_args.append('-o' + output_file)
        if extra_preargs:
            pp_args[:0] = extra_preargs
        if extra_postargs:
            pp_args.extend(extra_postargs)
        pp_args.append(source)

        # We need to preprocess: either we're being forced to, or the
        # source file is newer than the target (or the target doesn't
        # exist).
        if self.force or output_file is None or newer(source, output_file):
            if output_file:
                self.mkpath(os.path.dirname(output_file))
            try:
                self.spawn(pp_args)
            except DistutilsExecError as msg:
                print(msg)
                raise CompileError(msg)