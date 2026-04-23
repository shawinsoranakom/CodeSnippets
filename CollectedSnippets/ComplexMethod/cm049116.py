def create(self, vals_list):
        to_update_drivers_cars = set()
        to_update_drivers_bikes = set()
        state_waiting_list = self.env.ref('fleet.fleet_vehicle_state_waiting_list', raise_if_not_found=False)
        for vals in vals_list:
            if vals.get('future_driver_id'):
                state_id = vals.get('state_id')
                if not state_waiting_list or state_waiting_list.id != state_id:
                    future_driver = vals['future_driver_id']
                    if vals.get('vehicle_type') == 'bike':
                        to_update_drivers_bikes.add(future_driver)
                    elif vals.get('vehicle_type') == 'car':
                        to_update_drivers_cars.add(future_driver)
        if to_update_drivers_cars:
            self.search([
                ('driver_id', 'in', to_update_drivers_cars),
                ('vehicle_type', '=', 'car'),
            ]).plan_to_change_car = True
        if to_update_drivers_bikes:
            self.search([
                ('driver_id', 'in', to_update_drivers_bikes),
                ('vehicle_type', '=', 'bike'),
            ]).plan_to_change_bike = True

        vehicles = super().create(vals_list)

        for vehicle, vals in zip(vehicles, vals_list):
            if vals.get('driver_id'):
                vehicle.create_driver_history(vals)
        return vehicles