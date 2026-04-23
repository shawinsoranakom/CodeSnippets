def execute(cls, images, vae, clip, texts=None):
        # Extract scalars (vae and clip are single values wrapped in lists)
        vae = vae[0]
        clip = clip[0]

        # Handle text list
        num_images = len(images)

        if texts is None or len(texts) == 0:
            # Treat as [""] for unconditional training
            texts = [""]

        if len(texts) == 1 and num_images > 1:
            # Repeat single text for all images
            texts = texts * num_images
        elif len(texts) != num_images:
            raise ValueError(
                f"Number of texts ({len(texts)}) does not match number of images ({num_images}). "
                f"Text list should have length {num_images}, 1, or 0."
            )

        # Encode images with VAE
        logging.info(f"Encoding {num_images} images with VAE...")
        latents_list = []  # list[{"samples": tensor}]
        for img_tensor in images:
            # img_tensor is [1, H, W, 3]
            latent_tensor = vae.encode(img_tensor[:, :, :, :3])
            latents_list.append({"samples": latent_tensor})

        # Encode texts with CLIP
        logging.info(f"Encoding {len(texts)} texts with CLIP...")
        conditioning_list = []  # list[list[cond]]
        for text in texts:
            if text == "":
                cond = clip.encode_from_tokens_scheduled(clip.tokenize(""))
            else:
                tokens = clip.tokenize(text)
                cond = clip.encode_from_tokens_scheduled(tokens)
            conditioning_list.append(cond)

        logging.info(
            f"Created dataset with {len(latents_list)} latents and {len(conditioning_list)} conditioning."
        )
        return io.NodeOutput(latents_list, conditioning_list)