def test_raises_runtimeerror(self):
        msg = "Script does-not-exist does not exist."
        with self.assertRaisesMessage(RuntimeError, msg):
            autoreload.get_child_arguments()