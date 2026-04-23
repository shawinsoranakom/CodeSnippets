def run(self, pp: PostprocessedImage, args):
        scripts = []

        for script in self.scripts_in_preferred_order():
            script_args = args[script.args_from:script.args_to]

            process_args = {}
            for (name, _component), value in zip(script.controls.items(), script_args):
                process_args[name] = value

            scripts.append((script, process_args))

        for script, process_args in scripts:
            script.process_firstpass(pp, **process_args)

        all_images = [pp]

        for script, process_args in scripts:
            if shared.state.skipped:
                break

            shared.state.job = script.name

            for single_image in all_images.copy():

                if not single_image.disable_processing:
                    script.process(single_image, **process_args)

                for extra_image in single_image.extra_images:
                    if not isinstance(extra_image, PostprocessedImage):
                        extra_image = single_image.create_copy(extra_image)

                    all_images.append(extra_image)

                single_image.extra_images.clear()

        pp.extra_images = all_images[1:]