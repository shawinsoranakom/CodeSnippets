def _remove_aux_file(self):
        pam_file = self.rs_path + ".aux.xml"
        if os.path.isfile(pam_file):
            os.remove(pam_file)