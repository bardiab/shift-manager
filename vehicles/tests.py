import pytest

from vehicles.models import Vehicle, Shift, VehicleShift
from vehicles.services import (
    add_vehicles_to_shift,
    auto_create_shift,
    create_shift,
    is_swap_completed,
    is_shift_completed,
    get_vehicles_in_shift,
    swap_vehicle_battery,
)
from django.contrib.gis.geos import Point


@pytest.fixture
def vehicles_setup():
    return {
        # lat long points from v1-v4 correspond to places from bottom -> top of manhattan
        "v1": Vehicle.objects.create(license_plate="NY001", battery_level=21.0,
                                     model='NIU', location_lat=40.712134, location_long=-74.006245),
        "v2": Vehicle.objects.create(license_plate="NY002", battery_level=100.0,
                                     model='NIU', location_lat=40.726186, location_long=-73.999031),
        "v3": Vehicle.objects.create(license_plate="NY003", battery_level=100.0,
                                     model='NIU', location_lat=40.751679, location_long=-73.980479),
        "v4": Vehicle.objects.create(license_plate="NY004", battery_level=100.0,
                                     model='NIU', location_lat=40.781841, location_long=-73.956087),
    }


@pytest.fixture
def shift_setup():
    return {
        "s1": Shift.objects.create(),
        "s2": Shift.objects.create(),
    }


@pytest.fixture
def vehicle_shift_setup(vehicles_setup, shift_setup):
    return {
        "vs1": VehicleShift.objects.create(vehicle=vehicles_setup['v1'], shift=shift_setup['s1']),
        "vs2": VehicleShift.objects.create(vehicle=vehicles_setup['v2'], shift=shift_setup['s1']),
        "vs3": VehicleShift.objects.create(vehicle=vehicles_setup['v3'], shift=shift_setup['s1']),
        "vs4": VehicleShift.objects.create(vehicle=vehicles_setup['v4'], shift=shift_setup['s1'])
    }


@pytest.mark.django_db
def test_create_shift():
    s: Shift = create_shift()

    assert Shift.objects.count() == 1
    assert s.completed is False


@pytest.mark.django_db
def test_add_vehicles_to_shift(vehicles_setup, shift_setup):
    v1 = vehicles_setup['v1']
    v2 = vehicles_setup['v2']
    v3 = vehicles_setup['v3']
    vehicles = [v1, v2, v3]
    vehicle_ids = [x.id for x in vehicles]

    s1 = shift_setup['s1']

    add_vehicles_to_shift(vehicle_ids=vehicle_ids, shift_id=s1.id)
    assert VehicleShift.objects.count() == 3

    s2 = shift_setup['s2']
    add_vehicles_to_shift(vehicle_ids=vehicle_ids, shift_id=s2.id)
    # none of these are added since they're already in shift s1
    assert VehicleShift.objects.count() == 3


@pytest.mark.django_db
def test_get_vehicles_in_shift(vehicle_shift_setup, shift_setup):
    shift = shift_setup['s1']
    vehicles = get_vehicles_in_shift(shift_id=shift.id)

    assert len(vehicles) == 4


@pytest.mark.django_db
def test_swap_vehicle_battery(vehicles_setup, vehicle_shift_setup):
    v1 = vehicles_setup['v1']
    vs = VehicleShift.objects.get(vehicle=v1)
    assert vs.swap_completed is False

    v = swap_vehicle_battery(vehicle_id=v1.id)
    vs.refresh_from_db()

    assert v.battery_level == 100
    assert vs.swap_completed is True


@pytest.mark.django_db
def test_is_swap_completed(vehicle_shift_setup, vehicles_setup, shift_setup):
    v1 = vehicles_setup['v1']
    s1 = shift_setup['s1']

    completed = is_swap_completed(vehicle_id=v1.id, shift_id=s1.id)
    assert completed is False

    swap_vehicle_battery(vehicle_id=v1.id)
    completed = is_swap_completed(vehicle_id=v1.id, shift_id=s1.id)
    assert completed is True


@pytest.mark.django_db
def test_is_shift_completed_yes(vehicle_shift_setup, vehicles_setup, shift_setup):
    s1 = shift_setup['s1']
    v1, v2, v3, v4 = vehicles_setup['v1'], vehicles_setup['v2'], vehicles_setup['v3'], vehicles_setup['v4']

    swap_vehicle_battery(vehicle_id=v1.id)
    swap_vehicle_battery(vehicle_id=v2.id)
    swap_vehicle_battery(vehicle_id=v3.id)
    swap_vehicle_battery(vehicle_id=v4.id)

    completed = is_shift_completed(shift_id=s1.id)
    assert completed is True


@pytest.mark.django_db
def test_is_shift_completed_no(vehicle_shift_setup, vehicles_setup, shift_setup):
    s1 = shift_setup['s1']
    v1, v2, v3, v4 = vehicles_setup['v1'], vehicles_setup['v2'], vehicles_setup['v3'], vehicles_setup['v4']

    swap_vehicle_battery(vehicle_id=v1.id)

    completed = is_shift_completed(shift_id=s1.id)
    assert completed is False


@pytest.mark.django_db
def test_auto_create_shift(vehicles_setup):
    # somewhere in dumbo
    long, lat = -73.992226, 40.694891
    curr_location = Point(long, lat)

    vehicles_in_shift = auto_create_shift(lat, long)

    closest_vehicle = vehicles_in_shift[0]
    second_closest = vehicles_in_shift[1]

    d1 = curr_location.distance(closest_vehicle.location)
    d2 = curr_location.distance(second_closest.location)
    assert d1 <= d2

    assert Shift.objects.count() == 1
    assert VehicleShift.objects.count() == 4

    s = Shift.objects.all().first()
    vs = VehicleShift.objects.all().first()
    assert vs.shift == s


