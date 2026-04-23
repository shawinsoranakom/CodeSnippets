def build_address(name, address):
        if "@" in address:
            return Address(display_name=name, addr_spec=address)
        return Address(display_name=name, username=address, domain="")