def as_c(self, where: str) -> str:
        """Dump this hole as a call to a patch_* function."""
        if self.void:
            return ""
        if self.custom_location:
            location = self.custom_location
        else:
            location = f"{where} + {self.offset:#x}"
        if self.custom_value:
            value = self.custom_value
        else:
            value = _HOLE_EXPRS[self.value]
            if self.symbol:
                if value:
                    value += " + "
                if self.symbol.startswith("CONST"):
                    value += f"instruction->{self.symbol[10:].lower()}"
                else:
                    value += f"(uintptr_t)&{self.symbol}"
            if _signed(self.addend) or not value:
                if value:
                    value += " + "
                value += f"{_signed(self.addend):#x}"
        if self.need_state:
            return f"{self.func}({location}, {value}, state);"
        if self.offset2 >= 0:
            first_location = f"{where} + {self.offset2:#x}"
            return f"{self.func}({first_location}, {location}, {value});"
        return f"{self.func}({location}, {value});"