def get_metadata_table(self, name):
        table = super().get_metadata_table(name)
        item = self.page.items.get(name, {})
        metadata = item.get("metadata") or {}

        keys = {
            'ss_output_name': "Output name:",
            'ss_sd_model_name': "Model:",
            'ss_clip_skip': "Clip skip:",
            'ss_network_module': "Kohya module:",
        }

        for key, label in keys.items():
            value = metadata.get(key, None)
            if value is not None and str(value) != "None":
                table.append((label, html.escape(value)))

        ss_training_started_at = metadata.get('ss_training_started_at')
        if ss_training_started_at:
            table.append(("Date trained:", datetime.datetime.utcfromtimestamp(float(ss_training_started_at)).strftime('%Y-%m-%d %H:%M')))

        ss_bucket_info = metadata.get("ss_bucket_info")
        if ss_bucket_info and "buckets" in ss_bucket_info:
            resolutions = {}
            for _, bucket in ss_bucket_info["buckets"].items():
                resolution = bucket["resolution"]
                resolution = f'{resolution[1]}x{resolution[0]}'

                resolutions[resolution] = resolutions.get(resolution, 0) + int(bucket["count"])

            resolutions_list = sorted(resolutions.keys(), key=resolutions.get, reverse=True)
            resolutions_text = html.escape(", ".join(resolutions_list[0:4]))
            if len(resolutions) > 4:
                resolutions_text += ", ..."
                resolutions_text = f"<span title='{html.escape(', '.join(resolutions_list))}'>{resolutions_text}</span>"

            table.append(('Resolutions:' if len(resolutions_list) > 1 else 'Resolution:', resolutions_text))

        image_count = 0
        for _, params in metadata.get("ss_dataset_dirs", {}).items():
            image_count += int(params.get("img_count", 0))

        if image_count:
            table.append(("Dataset size:", image_count))

        return table