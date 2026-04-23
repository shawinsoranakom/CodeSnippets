def test_non_ascii_attachment_filename(self):
        """Regression test for #14964"""
        msg = EmailMessage(body="Content")
        # Unicode in file name
        msg.attach("une pièce jointe.pdf", b"%PDF-1.4.%...", mimetype="application/pdf")
        attachment = self.get_decoded_attachments(msg)[0]
        self.assertEqual(attachment.filename, "une pièce jointe.pdf")