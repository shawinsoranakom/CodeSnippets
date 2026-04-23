def save_preview(index, images, filename):
        # this function is here for backwards compatibility and likely will be removed soon

        if len(images) == 0:
            print("There is no image in gallery to save as a preview.")
            return [page.create_html(ui.tabname) for page in ui.stored_extra_pages]

        index = int(index)
        index = 0 if index < 0 else index
        index = len(images) - 1 if index >= len(images) else index

        img_info = images[index if index >= 0 else 0]
        image = image_from_url_text(img_info)
        geninfo, items = read_info_from_image(image)

        is_allowed = False
        for extra_page in ui.stored_extra_pages:
            if any(path_is_parent(x, filename) for x in extra_page.allowed_directories_for_previews()):
                is_allowed = True
                break

        assert is_allowed, f'writing to {filename} is not allowed'

        save_image_with_geninfo(image, geninfo, filename)

        return [page.create_html(ui.tabname) for page in ui.stored_extra_pages]