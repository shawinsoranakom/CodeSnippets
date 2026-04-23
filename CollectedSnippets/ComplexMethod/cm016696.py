def flat_and_pad_to_seq(self, hidden_states, ref_image_hidden_states):
        batch_size = len(hidden_states)
        p = self.patch_size

        img_sizes = [(img.size(1), img.size(2)) for img in hidden_states]
        l_effective_img_len = [(H // p) * (W // p) for (H, W) in img_sizes]

        if ref_image_hidden_states is not None:
            ref_image_hidden_states = list(map(lambda ref: comfy.ldm.common_dit.pad_to_patch_size(ref, (p, p)), ref_image_hidden_states))
            ref_img_sizes = [[(imgs.size(2), imgs.size(3)) if imgs is not None else None for imgs in ref_image_hidden_states]] * batch_size
            l_effective_ref_img_len = [[(ref_img_size[0] // p) * (ref_img_size[1] // p) for ref_img_size in _ref_img_sizes] if _ref_img_sizes is not None else [0] for _ref_img_sizes in ref_img_sizes]
        else:
            ref_img_sizes = [None for _ in range(batch_size)]
            l_effective_ref_img_len = [[0] for _ in range(batch_size)]

        flat_ref_img_hidden_states = None
        if ref_image_hidden_states is not None:
            imgs = []
            for ref_img in ref_image_hidden_states:
                B, C, H, W = ref_img.size()
                ref_img = rearrange(ref_img, 'b c (h p1) (w p2) -> b (h w) (p1 p2 c)', p1=p, p2=p)
                imgs.append(ref_img)
            flat_ref_img_hidden_states = torch.cat(imgs, dim=1)

        img = hidden_states
        B, C, H, W = img.size()
        flat_hidden_states = rearrange(img, 'b c (h p1) (w p2) -> b (h w) (p1 p2 c)', p1=p, p2=p)

        return (
            flat_hidden_states, flat_ref_img_hidden_states,
            None, None,
            l_effective_ref_img_len, l_effective_img_len,
            ref_img_sizes, img_sizes,
        )