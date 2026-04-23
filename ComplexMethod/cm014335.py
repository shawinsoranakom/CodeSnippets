def _hipify_compile_flags(self, extension) -> None:
        if isinstance(extension.extra_compile_args, dict) and 'nvcc' in extension.extra_compile_args:
            modified_flags = []
            for flag in extension.extra_compile_args['nvcc']:
                if flag.startswith("-") and "CUDA" in flag and not flag.startswith("-I"):
                    # check/split flag into flag and value
                    parts = flag.split("=", 1)
                    if len(parts) == 2:
                        flag_part, value_part = parts
                        # replace fist instance of "CUDA" with "HIP" only in the flag and not flag value
                        modified_flag_part = flag_part.replace("CUDA", "HIP", 1)
                        modified_flag = f"{modified_flag_part}={value_part}"
                    else:
                        # replace fist instance of "CUDA" with "HIP" in flag
                        modified_flag = flag.replace("CUDA", "HIP", 1)
                    modified_flags.append(modified_flag)
                    logger.info('Modified flag: %s -> %s', flag, modified_flag)
                else:
                    modified_flags.append(flag)
            extension.extra_compile_args['nvcc'] = modified_flags