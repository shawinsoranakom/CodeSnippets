def _compute_display_name(self):
        show_dest_package = self.env.context.get('show_dest_package')
        show_src_package = self.env.context.get('show_src_package')
        is_done = self.env.context.get('is_done')
        for package in self:
            if is_done:
                display_name = package.name
            elif show_dest_package:
                display_name = package.dest_complete_name
            elif show_src_package:
                display_name = package.complete_name
            else:
                display_name = package.name

            if package.env.context.get('formatted_display_name') and package.package_type_id and package.package_type_id.packaging_length and package.package_type_id.width and package.package_type_id.height:
                package.display_name = f"{display_name}\t--{package.package_type_id.packaging_length} x {package.package_type_id.width} x {package.package_type_id.height}--"
            else:
                package.display_name = display_name