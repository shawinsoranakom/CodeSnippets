def test_file_multiple_validation(self):
        f = MultipleFileField(validators=[validate_image_file_extension])

        good_files = [
            SimpleUploadedFile("image1.jpg", b"fake JPEG"),
            SimpleUploadedFile("image2.png", b"faux image"),
            SimpleUploadedFile("image3.bmp", b"fraudulent bitmap"),
        ]
        self.assertEqual(f.clean(good_files), good_files)

        evil_files = [
            SimpleUploadedFile("image1.sh", b"#!/bin/bash -c 'echo pwned!'\n"),
            SimpleUploadedFile("image2.png", b"faux image"),
            SimpleUploadedFile("image3.jpg", b"fake JPEG"),
        ]

        evil_rotations = (
            evil_files[i:] + evil_files[:i]  # Rotate by i.
            for i in range(len(evil_files))
        )
        msg = "File extension “sh” is not allowed. Allowed extensions are: "
        for rotated_evil_files in evil_rotations:
            with self.assertRaisesMessage(ValidationError, msg):
                f.clean(rotated_evil_files)