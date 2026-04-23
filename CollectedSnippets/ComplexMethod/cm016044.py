def gen_wrappers(xnnpack_path):
    xnnpack_sources = collections.defaultdict(list)
    sources = update_sources(xnnpack_path)

    microkernels_sources = update_sources(xnnpack_path, "XNNPACK/cmake/gen/microkernels.cmake")
    for key in  microkernels_sources:
        sources[key] = microkernels_sources[key]

    for name in WRAPPER_SRC_NAMES:
        xnnpack_sources[WRAPPER_SRC_NAMES[name]].extend(sources[name])

    for condition, filenames in xnnpack_sources.items():
        print(condition)
        for filename in filenames:
            filepath = os.path.join(xnnpack_path, "xnnpack_wrappers", filename)

            if not os.path.isdir(os.path.dirname(filepath)):
                os.makedirs(os.path.dirname(filepath))
            with open(filepath, "w") as wrapper:
                print(f"/* {BANNER} */", file=wrapper)
                print(file=wrapper)

                # Architecture- or platform-dependent preprocessor flags can be
                # defined here. Note: platform_preprocessor_flags can't be used
                # because they are ignored by arc focus & buck project.

                if condition is None:
                    print(f"#include <{filename}>", file=wrapper)
                else:
                    # Include source file only if condition is satisfied
                    print(f"#if {condition}", file=wrapper)
                    print(f"#include <{filename}>", file=wrapper)
                    print(f"#endif /* {condition} */", file=wrapper)

    # update xnnpack_wrapper_defs.bzl file under the same folder
    with open(os.path.join(os.path.dirname(__file__), "xnnpack_wrapper_defs.bzl"), 'w') as wrapper_defs:
        print('"""', file=wrapper_defs)
        print(BANNER, file=wrapper_defs)
        print('"""', file=wrapper_defs)
        for name in WRAPPER_SRC_NAMES:
            print('\n' + name + ' = [', file=wrapper_defs)
            for file_name in sources[name]:
                print(f'    "xnnpack_wrappers/{file_name}",', file=wrapper_defs)
            print(']', file=wrapper_defs)

    # update xnnpack_src_defs.bzl file under the same folder
    with open(os.path.join(os.path.dirname(__file__), "xnnpack_src_defs.bzl"), 'w') as src_defs:
        print('"""', file=src_defs)
        print(BANNER, file=src_defs)
        print('"""', file=src_defs)
        for name in SRC_NAMES:
            print('\n' + name + ' = [', file=src_defs)
            for file_name in sources[name]:
                print(f'    "XNNPACK/src/{file_name}",', file=src_defs)
            print(']', file=src_defs)