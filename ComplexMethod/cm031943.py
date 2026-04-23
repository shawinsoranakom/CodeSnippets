def preprocess(self, source, output_file=None, macros=None,
                   include_dirs=None, extra_preargs=None, extra_postargs=None):
        fixed_args = self._fix_compile_args(None, macros, include_dirs)
        ignore, macros, include_dirs = fixed_args
        pp_opts = gen_preprocess_options(macros, include_dirs)
        pp_args = self.preprocessor + pp_opts
        if output_file:
            pp_args.extend(['-o', output_file])
        if extra_preargs:
            pp_args[:0] = extra_preargs
        if extra_postargs:
            pp_args.extend(extra_postargs)
        pp_args.append(source)

        # We need to preprocess: either we're being forced to, or we're
        # generating output to stdout, or there's a target output file and
        # the source file is newer than the target (or the target doesn't
        # exist).
        if self.force or output_file is None or newer(source, output_file):
            if output_file:
                self.mkpath(os.path.dirname(output_file))
            try:
                self.spawn(pp_args)
            except DistutilsExecError as msg:
                raise CompileError(msg)