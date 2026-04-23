def unix_wrap_ninja_compile(sources,
                                    output_dir=None,
                                    macros=None,
                                    include_dirs=None,
                                    debug=0,
                                    extra_preargs=None,
                                    extra_postargs=None,
                                    depends=None):
            r"""Compiles sources by outputting a ninja file and running it."""
            # NB: I copied some lines from self.compiler (which is an instance
            # of distutils.UnixCCompiler). See the following link.
            # https://github.com/python/cpython/blob/f03a8f8d5001963ad5b5b28dbd95497e9cc15596/Lib/distutils/ccompiler.py#L564-L567  # codespell:ignore
            # This can be fragile, but a lot of other repos also do this
            # (see https://github.com/search?q=_setup_compile&type=Code)
            # so it is probably OK; we'll also get CI signal if/when
            # we update our python version (which is when distutils can be
            # upgraded)

            # Use absolute path for output_dir so that the object file paths
            # (`objects`) get generated with absolute paths.
            # pyrefly: ignore [no-matching-overload]
            output_dir = os.path.abspath(output_dir)

            # See Note [Absolute include_dirs]
            convert_to_absolute_paths_inplace(self.compiler.include_dirs)

            _, objects, extra_postargs, pp_opts, _ = \
                self.compiler._setup_compile(output_dir, macros,
                                             include_dirs, sources,
                                             depends, extra_postargs)
            common_cflags = self.compiler._get_cc_args(pp_opts, debug, extra_preargs)
            extra_cc_cflags = self.compiler.compiler_so[1:]
            with_cuda = any(map(_is_cuda_file, sources))
            with_sycl = any(map(_is_sycl_file, sources))
            if with_sycl and with_cuda:
                raise AssertionError(
                    "cannot have both SYCL and CUDA files in the same extension"
                )

            # extra_postargs can be either:
            # - a dict mapping cxx/nvcc/sycl to extra flags
            # - a list of extra flags.
            if isinstance(extra_postargs, dict):
                post_cflags = extra_postargs['cxx']
            else:
                post_cflags = list(extra_postargs)
            if IS_HIP_EXTENSION:
                post_cflags = COMMON_HIP_FLAGS + post_cflags
            append_std17_if_no_std_present(post_cflags)

            cuda_post_cflags = None
            cuda_cflags = None
            if with_cuda:
                cuda_cflags = common_cflags
                if isinstance(extra_postargs, dict):
                    cuda_post_cflags = extra_postargs['nvcc']
                else:
                    cuda_post_cflags = list(extra_postargs)
                if IS_HIP_EXTENSION:
                    cuda_post_cflags = cuda_post_cflags + _get_rocm_arch_flags(cuda_post_cflags)
                    cuda_post_cflags = COMMON_HIP_FLAGS + COMMON_HIPCC_FLAGS + cuda_post_cflags
                else:
                    cuda_post_cflags = unix_cuda_flags(cuda_post_cflags)
                append_std17_if_no_std_present(cuda_post_cflags)
                cuda_cflags = [shlex.quote(f) for f in cuda_cflags]
                cuda_post_cflags = [shlex.quote(f) for f in cuda_post_cflags]

            if isinstance(extra_postargs, dict) and 'nvcc_dlink' in extra_postargs:
                cuda_dlink_post_cflags = unix_cuda_flags(extra_postargs['nvcc_dlink'])
                cuda_dlink_post_cflags = [shlex.quote(f) for f in cuda_dlink_post_cflags]
            else:
                cuda_dlink_post_cflags = None

            sycl_post_cflags = None
            sycl_cflags = None
            sycl_dlink_post_cflags = None
            if with_sycl:
                sycl_cflags = extra_cc_cflags + common_cflags + _COMMON_SYCL_FLAGS
                if isinstance(extra_postargs, dict):
                    sycl_post_cflags = extra_postargs['sycl']
                else:
                    sycl_post_cflags = list(extra_postargs)
                _append_sycl_targets_if_missing(sycl_post_cflags)
                append_std17_if_no_std_present(sycl_cflags)
                _append_sycl_std_if_no_std_present(sycl_cflags)
                host_cflags = extra_cc_cflags + common_cflags + post_cflags
                append_std17_if_no_std_present(host_cflags)
                # escaping quoted arguments to pass them thru SYCL compiler
                icpx_version = _get_icpx_version()
                if int(icpx_version) >= 20250200:
                    host_cflags = [item.replace('"', '\\"') for item in host_cflags]
                else:
                    host_cflags = [item.replace('"', '\\\\"') for item in host_cflags]
                # Note the order: shlex.quote sycl_flags first, _wrap_sycl_host_flags
                # second. Reason is that sycl host flags are quoted, space containing
                # strings passed to SYCL compiler.
                sycl_cflags = [shlex.quote(f) for f in sycl_cflags]
                sycl_cflags += _wrap_sycl_host_flags(host_cflags)
                sycl_dlink_post_cflags = _SYCL_DLINK_FLAGS.copy()
                sycl_dlink_post_cflags += _get_sycl_device_flags(sycl_post_cflags)
                sycl_post_cflags = [shlex.quote(f) for f in sycl_post_cflags]

            _write_ninja_file_and_compile_objects(
                sources=sources,
                objects=objects,
                cflags=[shlex.quote(f) for f in extra_cc_cflags + common_cflags],
                post_cflags=[shlex.quote(f) for f in post_cflags],
                cuda_cflags=cuda_cflags,
                cuda_post_cflags=cuda_post_cflags,
                cuda_dlink_post_cflags=cuda_dlink_post_cflags,
                sycl_cflags=sycl_cflags,
                sycl_post_cflags=sycl_post_cflags,
                sycl_dlink_post_cflags=sycl_dlink_post_cflags,
                build_directory=output_dir,
                verbose=True,
                with_cuda=with_cuda,
                with_sycl=with_sycl)

            # Return *all* object filenames, not just the ones we just built.
            return objects