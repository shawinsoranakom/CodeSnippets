def load_from_file(self, path, filename):
        name, ext = os.path.splitext(filename)
        ext = ext.upper()

        if ext in ['.PNG', '.WEBP', '.JXL', '.AVIF']:
            _, second_ext = os.path.splitext(name)
            if second_ext.upper() == '.PREVIEW':
                return

            embed_image = Image.open(path)
            if hasattr(embed_image, 'text') and 'sd-ti-embedding' in embed_image.text:
                data = embedding_from_b64(embed_image.text['sd-ti-embedding'])
                name = data.get('name', name)
            else:
                data = extract_image_data_embed(embed_image)
                if data:
                    name = data.get('name', name)
                else:
                    # if data is None, means this is not an embedding, just a preview image
                    return
        elif ext in ['.BIN', '.PT']:
            data = torch.load(path, map_location="cpu")
        elif ext in ['.SAFETENSORS']:
            data = safetensors.torch.load_file(path, device="cpu")
        else:
            return

        if data is not None:
            embedding = create_embedding_from_data(data, name, filename=filename, filepath=path)

            if self.expected_shape == -1 or self.expected_shape == embedding.shape:
                self.register_embedding(embedding, shared.sd_model)
            else:
                self.skipped_embeddings[name] = embedding
        else:
            print(f"Unable to load Textual inversion embedding due to data issue: '{name}'.")