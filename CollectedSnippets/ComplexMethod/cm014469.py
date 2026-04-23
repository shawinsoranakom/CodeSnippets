def get_hip_file_path(rel_filepath, is_pytorch_extension=False):
    """
    Returns the new name of the hipified file
    """
    # At the moment, some PyTorch source files are HIPified in place.  The predicate
    # is_out_of_place tells us if this is the case or not.
    if os.path.isabs(rel_filepath):
        raise AssertionError("rel_filepath must be a relative path")
    if not is_pytorch_extension and not is_out_of_place(rel_filepath):
        return rel_filepath

    dirpath, filename = os.path.split(rel_filepath)
    root, ext = os.path.splitext(filename)

    # Here's the plan:
    #
    # In general, we need to disambiguate the HIPified filename so that
    # it gets a different name from the original filename, so
    # that we don't overwrite the original file
    #
    # There's a lot of different naming conventions across PyTorch,
    # but the general recipe is to convert occurrences
    # of cuda/gpu to hip, and add hip if there are no occurrences
    # of cuda/gpu anywhere.
    #
    # Concretely, we do the following:
    #
    #   - If there is a directory component named "cuda", replace
    #     it with "hip", AND
    #
    #   - If the file name contains "CUDA", replace it with "HIP", AND
    #
    #   - ALWAYS replace '.cu' with '.hip', because those files
    #     contain CUDA kernels that needs to be hipified and processed with
    #     hip compiler
    #
    #   - If we are not hipifying a PyTorch extension, and the parent
    #     directory name did not change as a result of the above
    #     transformations, insert "hip" in the file path
    #     as the direct parent folder of the file
    #
    #   - If we are hipifying a PyTorch extension, and the parent directory
    #     name as well as the filename (incl. extension) did not change as
    #     a result of the above transformations, insert "_hip" in the filename
    #
    # This isn't set in stone; we might adjust this to support other
    # naming conventions.

    if ext == '.cu':
        ext = '.hip'

    orig_filename = filename
    orig_dirpath = dirpath

    dirpath = dirpath.replace('cuda', 'hip')
    dirpath = dirpath.replace('CUDA', 'HIP')
    dirpath = dirpath.replace('THC', 'THH')

    root = root.replace('cuda', 'hip')
    root = root.replace('CUDA', 'HIP')
    # Special case to handle caffe2/core/THCCachingAllocator
    if dirpath != "caffe2/core":
        root = root.replace('THC', 'THH')

    if not is_pytorch_extension and dirpath == orig_dirpath:
        dirpath = os.path.join(dirpath, 'hip')

    if is_pytorch_extension and dirpath == orig_dirpath and (root + ext) == orig_filename:
        root = root + "_hip"

    return os.path.join(dirpath, root + ext)