import base64
from typing import List

from vehicles.models import Shift, Vehicle, VehicleShift

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance


def create_shift() -> Shift:
    s = Shift.objects.create()
    return s


def add_vehicles_to_shift(vehicle_ids: List[str], shift_id: str) -> List[VehicleShift]:
    vehicles = Vehicle.objects.filter(id__in=vehicle_ids)
    try:
        s = Shift.objects.get(id=shift_id)
    except Shift.DoesNotExist:
        raise Exception("Unable to retrieve shift")

    vs_to_create = []
    for v in vehicles:
        # don't add a vehicle to a shift if its already in one
        vehicle_in_shift = VehicleShift.objects.filter(vehicle_id=v.id)
        if not vehicle_in_shift:
            vs_to_create.append(
                VehicleShift(vehicle=v, shift=s)
            )
    vs = VehicleShift.objects.bulk_create(vs_to_create, ignore_conflicts=True)
    return vs


def get_vehicles_in_shift(shift_id: str) -> List[Vehicle]:
    vs = VehicleShift.objects.filter(shift_id=shift_id)
    vehicles = Vehicle.objects.filter(id__in=vs.values('vehicle_id'))
    return vehicles


def swap_vehicle_battery(vehicle_id: str) -> Vehicle:
    # assume swapping a battery means replacing it with an infinite supply
    # of batteries charged to 100%
    try:
        v: Vehicle = Vehicle.objects.get(id=vehicle_id)
        v.battery_level = 100.0
        v.save(update_fields=['battery_level'])
    except Vehicle.DoesNotExist:
        raise Exception("Unable to find vehicle")

    try:
        vs = VehicleShift.objects.get(vehicle=v)
        vs.swap_completed = True
        vs.save(update_fields=['swap_completed'])
    except VehicleShift.DoesNotExist:
        raise Exception("Unable to retrieve vehicle in shift")

    return v


def is_swap_completed(vehicle_id: str, shift_id: str) -> bool:
    try:
        vs = VehicleShift.objects.get(vehicle_id=vehicle_id, shift_id=shift_id)
    except VehicleShift.DoesNotExist:
        raise Exception("Unable to find vehicle in shift")

    return vs.swap_completed


def is_shift_completed(shift_id: str) -> bool:
    vs: List[VehicleShift] = VehicleShift.objects.filter(shift_id=shift_id)
    shift = vs[0].shift
    if shift.completed:
        return True
    else:
        completed = all([x.swap_completed for x in vs])
        if completed:
            shift.completed = True
            shift.active = False
            shift.save(update_fields=['completed', 'active'])
        return completed


def auto_create_shift(lat: float, long: float) -> List[Vehicle]:
    """
    Select the 20 closest vehicles from lat, long and add them all to a newly
    created shift. Vehicles will be added to shift in the order they will be visited
    (closest distance to farthest).
    """
    curr_location = Point(long, lat)

    close_vehicles = Vehicle.objects.filter(
        location__distance_lte=(curr_location, D(mi=50))).annotate(
        distance=Distance('location', curr_location)).order_by('distance')[:20]

    shift = create_shift()
    v_ids = close_vehicles.values('id')
    add_vehicles_to_shift(vehicle_ids=v_ids, shift_id=shift.id)

    return close_vehicles





