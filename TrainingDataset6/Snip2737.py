def get_facility(facility_id: str) -> Facility:
        return Facility(
            id=facility_id,
            address=Address(line_1="123 Main St", city="Anytown", state_province="CA"),
        )