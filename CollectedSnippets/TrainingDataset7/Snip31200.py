def test_unicode_attachment(self):
        response = FileResponse(
            ContentFile(b"binary content", name="祝您平安.odt"),
            as_attachment=True,
            content_type="application/vnd.oasis.opendocument.text",
        )
        self.assertEqual(
            response.headers["Content-Type"],
            "application/vnd.oasis.opendocument.text",
        )
        self.assertEqual(
            response.headers["Content-Disposition"],
            "attachment; filename*=utf-8''%E7%A5%9D%E6%82%A8%E5%B9%B3%E5%AE%89.odt",
        )