def get_ds_file(name, ext):
    return os.path.join(TEST_DATA, name, name + ".%s" % ext)