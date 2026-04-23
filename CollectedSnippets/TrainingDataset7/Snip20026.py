def _check_referer_rejects(self, mw, req):
        with self.assertRaises(RejectRequest):
            mw._check_referer(req)