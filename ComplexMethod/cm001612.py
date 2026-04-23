def get_images(extras_mode, image, image_folder, input_dir):
        if extras_mode == 1:
            for img in image_folder:
                if isinstance(img, Image.Image):
                    image = images.fix_image(img)
                    fn = ''
                else:
                    image = images.read(os.path.abspath(img.name))
                    fn = os.path.splitext(img.orig_name)[0]
                yield image, fn
        elif extras_mode == 2:
            assert not shared.cmd_opts.hide_ui_dir_config, '--hide-ui-dir-config option must be disabled'
            assert input_dir, 'input directory not selected'

            image_list = shared.listfiles(input_dir)
            for filename in image_list:
                yield filename, filename
        else:
            assert image, 'image not selected'
            yield image, None