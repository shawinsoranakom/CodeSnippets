def dump(self, obj):
            # Return bytes as hex for text formatting
            return obj.ewkb.hex().encode()