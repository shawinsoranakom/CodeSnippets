def win_wrap_ninja_compile(sources,
                                   output_dir=None,
                                   macros=None,
                                   include_dirs=None,
                                   debug=0,
                                   extra_preargs=None,
                                   extra_postargs=None,
                                   depends=None,
                                   is_standalone=False):
            if not self.compiler.initialized:
                self.compiler.initialize()
            # pyrefly: ignore [no-matching-overload]
            output_dir = os.path.abspath(output_dir)

            # Note [Absolute include_dirs]
            # Convert relative path in self.compiler.include_dirs to absolute path if any.
            # For ninja build, the build location is not local, but instead, the build happens
            # in a script-created build folder. Thus, relative paths lose their correctness.
            # To be consistent with jit extension, we allow user to enter relative include_dirs
            # in setuptools.setup, and we convert the relative path to absolute path here.
            convert_to_absolute_paths_inplace(self.compiler.include_dirs)

            _, objects, extra_postargs, pp_opts, _ = \
                self.compiler._setup_compile(output_dir, macros,
                                             include_dirs, sources,
                                             depends, extra_postargs)
            # Replace space with \ when using hipcc (hipcc passes includes to clang without ""s so clang sees space in include paths as new argument)
            if IS_HIP_EXTENSION:
                pp_opts = ["-I{}".format(s[2:].replace(" ", "\\")) if s.startswith('-I') else s for s in pp_opts]
            common_cflags = extra_preargs or []
            cflags = []
            if debug:
                cflags.extend(self.compiler.compile_options_debug)
            else:
                cflags.extend(self.compiler.compile_options)
            cflags = cflags + common_cflags + pp_opts + COMMON_MSVC_FLAGS
            if IS_HIP_EXTENSION:
                _set_hipcc_runtime_lib(is_standalone, debug)
                common_cflags.extend(COMMON_HIP_FLAGS)
            else:
                common_cflags.extend(COMMON_MSVC_FLAGS)
            with_cuda = any(map(_is_cuda_file, sources))
            with_sycl = any(map(_is_sycl_file, sources))
            if with_sycl and with_cuda:
                raise AssertionError(
                    "cannot have both SYCL and CUDA files in the same extension"
                )

            # extra_postargs can be either:
            # - a dict mapping cxx/nvcc to extra flags
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
                cuda_cflags = ['-std=c++20']
                for common_cflag in common_cflags:
                    cuda_cflags.append('-Xcompiler')
                    cuda_cflags.append(common_cflag)
                if not IS_HIP_EXTENSION:
                    cuda_cflags.append('--use-local-env')
                    for ignore_warning in MSVC_IGNORE_CUDAFE_WARNINGS:
                        cuda_cflags.append('-Xcudafe')
                        cuda_cflags.append('--diag_suppress=' + ignore_warning)
                cuda_cflags.extend(pp_opts)
                if isinstance(extra_postargs, dict):
                    cuda_post_cflags = extra_postargs['nvcc']
                else:
                    cuda_post_cflags = list(extra_postargs)
                if IS_HIP_EXTENSION:
                    cuda_post_cflags = win_hip_flags(cuda_post_cflags)
                else:
                    cuda_post_cflags = win_cuda_flags(cuda_post_cflags)
            cflags = _nt_quote_args(cflags)
            post_cflags = _nt_quote_args(post_cflags)
            if with_cuda:
                cuda_cflags = _nt_quote_args(cuda_cflags)
                cuda_post_cflags = _nt_quote_args(cuda_post_cflags)
            if isinstance(extra_postargs, dict) and 'nvcc_dlink' in extra_postargs:
                cuda_dlink_post_cflags = win_cuda_flags(extra_postargs['nvcc_dlink'])
            else:
                cuda_dlink_post_cflags = None

            sycl_cflags = None
            sycl_post_cflags = None
            sycl_dlink_post_cflags = None
            if with_sycl:
                sycl_cflags = common_cflags + win_filter_msvc_include_dirs(pp_opts) + _COMMON_SYCL_FLAGS
                if isinstance(extra_postargs, dict):
                    sycl_post_cflags = extra_postargs['sycl']
                else:
                    sycl_post_cflags = list(extra_postargs)
                _append_sycl_targets_if_missing(sycl_post_cflags)
                append_std17_if_no_std_present(sycl_cflags)
                _append_sycl_std_if_no_std_present(sycl_cflags)
                host_cflags = common_cflags + pp_opts + post_cflags
                append_std17_if_no_std_present(host_cflags)

                sycl_cflags = _nt_quote_args(sycl_cflags)
                host_cflags = _nt_quote_args(host_cflags)

                sycl_cflags += _wrap_sycl_host_flags(host_cflags)
                sycl_dlink_post_cflags = _SYCL_DLINK_FLAGS.copy()
                sycl_dlink_post_cflags += _get_sycl_device_flags(sycl_post_cflags)
                sycl_post_cflags = _nt_quote_args(sycl_post_cflags)


            _write_ninja_file_and_compile_objects(
                sources=sources,
                objects=objects,
                cflags=cflags,
                post_cflags=post_cflags,
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