def get_image_file(self, x):
        import os, glob
        if len(x) == 0:             return False, None
        if not os.path.exists(x):   return False, None
        if x.endswith('.png'):      return True, x
        file_manifest = [f for f in glob.glob(f'{x}/**/*.png', recursive=True)]
        confirm = (len(file_manifest) >= 1 and file_manifest[0].endswith('.png') and os.path.exists(file_manifest[0]))
        file = None if not confirm else file_manifest[0]
        return confirm, file