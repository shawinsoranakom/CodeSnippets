def test_post_process_label_fusing(self):
        for image_processing_class in self.image_processing_classes.values():
            image_processor = image_processing_class(num_labels=self.image_processor_tester.num_classes)
            outputs = self.image_processor_tester.get_fake_maskformer_outputs()

            segmentation = image_processor.post_process_panoptic_segmentation(
                outputs, threshold=0, mask_threshold=0, overlap_mask_area_threshold=0
            )
            unfused_segments = [el["segments_info"] for el in segmentation]

            fused_segmentation = image_processor.post_process_panoptic_segmentation(
                outputs, threshold=0, mask_threshold=0, overlap_mask_area_threshold=0, label_ids_to_fuse={1}
            )
            fused_segments = [el["segments_info"] for el in fused_segmentation]

            for el_unfused, el_fused in zip(unfused_segments, fused_segments):
                if len(el_unfused) == 0:
                    self.assertEqual(len(el_unfused), len(el_fused))
                    continue

                # Get number of segments to be fused
                fuse_targets = [1 for el in el_unfused if el["label_id"] == 1]
                num_to_fuse = 0 if len(fuse_targets) == 0 else sum(fuse_targets) - 1
                # Expected number of segments after fusing
                expected_num_segments = max(el["id"] for el in el_unfused) - num_to_fuse
                num_segments_fused = max(el["id"] for el in el_fused)
                self.assertEqual(num_segments_fused, expected_num_segments)