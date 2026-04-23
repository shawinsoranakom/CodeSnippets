def clone_has_same_weights(self, clone: 'ModelPatcher'):
        if not self.is_clone(clone):
            return False

        if self.current_hooks != clone.current_hooks:
            return False
        if self.forced_hooks != clone.forced_hooks:
            return False
        if self.hook_patches.keys() != clone.hook_patches.keys():
            return False
        if self.attachments.keys() != clone.attachments.keys():
            return False
        if self.additional_models.keys() != clone.additional_models.keys():
            return False
        for key in self.callbacks:
            if len(self.callbacks[key]) != len(clone.callbacks[key]):
                return False
        for key in self.wrappers:
            if len(self.wrappers[key]) != len(clone.wrappers[key]):
                return False
        if self.injections.keys() != clone.injections.keys():
            return False

        if len(self.patches) == 0 and len(clone.patches) == 0:
            return True

        if self.patches_uuid == clone.patches_uuid:
            if len(self.patches) != len(clone.patches):
                logging.warning("WARNING: something went wrong, same patch uuid but different length of patches.")
            else:
                return True