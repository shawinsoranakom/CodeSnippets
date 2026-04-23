def keys_ok(self, keys):
        """Validity check on user's 'basic' keybinding selection.

        Doesn't check the string produced by the advanced dialog because
        'modifiers' isn't set.
        """
        final_key = self.list_keys_final.get('anchor')
        modifiers = self.get_modifiers()
        title = self.keyerror_title
        key_sequences = [key for keylist in self.current_key_sequences
                             for key in keylist]
        if not keys.endswith('>'):
            self.showerror(title, parent=self,
                           message='Missing the final Key')
        elif (not modifiers
              and final_key not in FUNCTION_KEYS + MOVE_KEYS):
            self.showerror(title=title, parent=self,
                           message='No modifier key(s) specified.')
        elif (modifiers == ['Shift']) \
                 and (final_key not in
                      FUNCTION_KEYS + MOVE_KEYS + ('Tab', 'Space')):
            msg = 'The shift modifier by itself may not be used with'\
                  ' this key symbol.'
            self.showerror(title=title, parent=self, message=msg)
        elif keys in key_sequences:
            msg = 'This key combination is already in use.'
            self.showerror(title=title, parent=self, message=msg)
        else:
            return True
        return False