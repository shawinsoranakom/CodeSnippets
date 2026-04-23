def process(self, pp: scripts_postprocessing.PostprocessedImage, upscale_enabled=True, upscale_mode=1, upscale_by=2.0, max_side_length=0, upscale_to_width=None, upscale_to_height=None, upscale_crop=False, upscaler_1_name=None, upscaler_2_name=None, upscaler_2_visibility=0.0):
        if not upscale_enabled:
            return

        upscaler_1_name = upscaler_1_name
        if upscaler_1_name == "None":
            upscaler_1_name = None

        upscaler1 = next(iter([x for x in shared.sd_upscalers if x.name == upscaler_1_name]), None)
        assert upscaler1 or (upscaler_1_name is None), f'could not find upscaler named {upscaler_1_name}'

        if not upscaler1:
            return

        upscaler_2_name = upscaler_2_name
        if upscaler_2_name == "None":
            upscaler_2_name = None

        upscaler2 = next(iter([x for x in shared.sd_upscalers if x.name == upscaler_2_name and x.name != "None"]), None)
        assert upscaler2 or (upscaler_2_name is None), f'could not find upscaler named {upscaler_2_name}'

        upscaled_image = self.upscale(pp.image, pp.info, upscaler1, upscale_mode, upscale_by, max_side_length, upscale_to_width, upscale_to_height, upscale_crop)
        pp.info["Postprocess upscaler"] = upscaler1.name

        if upscaler2 and upscaler_2_visibility > 0:
            second_upscale = self.upscale(pp.image, pp.info, upscaler2, upscale_mode, upscale_by, max_side_length, upscale_to_width, upscale_to_height, upscale_crop)
            if upscaled_image.mode != second_upscale.mode:
                second_upscale = second_upscale.convert(upscaled_image.mode)
            upscaled_image = Image.blend(upscaled_image, second_upscale, upscaler_2_visibility)

            pp.info["Postprocess upscaler 2"] = upscaler2.name

        pp.image = upscaled_image