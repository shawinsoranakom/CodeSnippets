def id_for_label(self, id_, index="0"):
        """
        Use an incremented id for each option where the main widget
        references the zero index.
        """
        if id_ and self.add_id_index:
            id_ = "%s_%s" % (id_, index)
        return id_