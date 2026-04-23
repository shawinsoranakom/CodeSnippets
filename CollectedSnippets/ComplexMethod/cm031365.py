def __setup_movement(self):
        """
        Set up the movement functions based on the terminal capabilities.
        """
        if 0 and self._hpa:  # hpa don't work in windows telnet :-(
            self.__move_x = self.__move_x_hpa
        elif self._cub and self._cuf:
            self.__move_x = self.__move_x_cub_cuf
        elif self._cub1 and self._cuf1:
            self.__move_x = self.__move_x_cub1_cuf1
        else:
            raise RuntimeError("insufficient terminal (horizontal)")

        if self._cuu and self._cud:
            self.__move_y = self.__move_y_cuu_cud
        elif self._cuu1 and self._cud1:
            self.__move_y = self.__move_y_cuu1_cud1
        else:
            raise RuntimeError("insufficient terminal (vertical)")

        if self._dch1:
            self.dch1 = self._dch1
        elif self._dch:
            self.dch1 = terminfo.tparm(self._dch, 1)
        else:
            self.dch1 = None

        if self._ich1:
            self.ich1 = self._ich1
        elif self._ich:
            self.ich1 = terminfo.tparm(self._ich, 1)
        else:
            self.ich1 = None

        self.__move = self.__move_short