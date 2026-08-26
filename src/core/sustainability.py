class SustainabilityEngine:
    @staticmethod
    def calculate_co2_and_logistics(cut_m3, fill_m3, transport_dist_km=15.0):
        saldo_m3 = abs(fill_m3 - cut_m3)
        truck_capacity_m3 = 14.0
        truck_trips = int(saldo_m3 / truck_capacity_m3) + (1 if saldo_m3 % truck_capacity_m3 > 0 else 0)
        fuel_consumption_liters = truck_trips * transport_dist_km * 2 * 0.38
        co2_tons = fuel_consumption_liters * 2.68 / 1000.0
        return {
            "truck_trips": truck_trips,
            "co2_emissions_tons": co2_tons,
            "fuel_liters": fuel_consumption_liters,
            "esg_compliant": co2_tons < 120.0
        }
