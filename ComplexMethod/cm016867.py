def _group_process(cls, images, similarity_threshold):
        """Remove duplicate images using perceptual hashing."""
        if len(images) == 0:
            return []

        # Compute simple perceptual hash for each image
        def compute_hash(img_tensor):
            """Compute a simple perceptual hash by resizing to 8x8 and comparing to average."""
            img = tensor_to_pil(img_tensor)
            # Resize to 8x8
            img_small = img.resize((8, 8), Image.Resampling.LANCZOS).convert("L")
            # Get pixels
            pixels = list(img_small.getdata())
            # Compute average
            avg = sum(pixels) / len(pixels)
            # Create hash (1 if above average, 0 otherwise)
            hash_bits = "".join("1" if p > avg else "0" for p in pixels)
            return hash_bits

        def hamming_distance(hash1, hash2):
            """Compute Hamming distance between two hash strings."""
            return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

        # Compute hashes for all images
        hashes = [compute_hash(img) for img in images]

        # Find duplicates
        keep_indices = []
        for i in range(len(images)):
            is_duplicate = False
            for j in keep_indices:
                # Compare hashes
                distance = hamming_distance(hashes[i], hashes[j])
                similarity = 1.0 - (distance / 64.0)  # 64 bits total
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    logging.info(
                        f"Image {i} is similar to image {j} (similarity: {similarity:.3f}), skipping"
                    )
                    break

            if not is_duplicate:
                keep_indices.append(i)

        # Return only unique images
        unique_images = [images[i] for i in keep_indices]
        logging.info(
            f"Deduplication: kept {len(unique_images)} out of {len(images)} images"
        )
        return unique_images