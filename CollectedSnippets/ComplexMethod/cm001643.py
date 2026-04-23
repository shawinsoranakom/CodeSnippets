def calculate_target_resolution(self):
        if opts.use_old_hires_fix_width_height and self.applied_old_hires_behavior_to != (self.width, self.height):
            self.hr_resize_x = self.width
            self.hr_resize_y = self.height
            self.hr_upscale_to_x = self.width
            self.hr_upscale_to_y = self.height

            self.width, self.height = old_hires_fix_first_pass_dimensions(self.width, self.height)
            self.applied_old_hires_behavior_to = (self.width, self.height)

        if self.hr_resize_x == 0 and self.hr_resize_y == 0:
            self.extra_generation_params["Hires upscale"] = self.hr_scale
            self.hr_upscale_to_x = int(self.width * self.hr_scale)
            self.hr_upscale_to_y = int(self.height * self.hr_scale)
        else:
            self.extra_generation_params["Hires resize"] = f"{self.hr_resize_x}x{self.hr_resize_y}"

            if self.hr_resize_y == 0:
                self.hr_upscale_to_x = self.hr_resize_x
                self.hr_upscale_to_y = self.hr_resize_x * self.height // self.width
            elif self.hr_resize_x == 0:
                self.hr_upscale_to_x = self.hr_resize_y * self.width // self.height
                self.hr_upscale_to_y = self.hr_resize_y
            else:
                target_w = self.hr_resize_x
                target_h = self.hr_resize_y
                src_ratio = self.width / self.height
                dst_ratio = self.hr_resize_x / self.hr_resize_y

                if src_ratio < dst_ratio:
                    self.hr_upscale_to_x = self.hr_resize_x
                    self.hr_upscale_to_y = self.hr_resize_x * self.height // self.width
                else:
                    self.hr_upscale_to_x = self.hr_resize_y * self.width // self.height
                    self.hr_upscale_to_y = self.hr_resize_y

                self.truncate_x = (self.hr_upscale_to_x - target_w) // opt_f
                self.truncate_y = (self.hr_upscale_to_y - target_h) // opt_f