from typing import List

import graphene

from graphene_django import DjangoObjectType
from vehicles.models import Vehicle, Shift, VehicleShift
from vehicles.services import (
    add_vehicles_to_shift,
    auto_create_shift,
    create_shift,
    get_vehicles_in_shift,
    is_shift_completed,
    is_swap_completed,
    swap_vehicle_battery,
)

class VehicleType(DjangoObjectType):
    class Meta:
        model = Vehicle
        exclude = (
            "location",
            "created",
            "modified",
        )

    distance = graphene.Float()

    def resolve_distance(self, info):
        d = getattr(self, 'distance', None)
        return round(d.mi, 2)


class ShiftType(DjangoObjectType):
    class Meta:
        model = Shift
        exclude = (
            "created",
            "modified",
        )


class VehicleShiftType(DjangoObjectType):
    class Meta:
        model = VehicleShift
        exclude = (
            "created",
            "modified",
        )


class Query(graphene.ObjectType):
    all_vehicles = graphene.List(VehicleType)
    vehicle = graphene.Field(VehicleType, vehicle_id=graphene.String(required=True))
    vehicles_in_shift = graphene.List(
        graphene.NonNull(VehicleType),
        shift_id=graphene.String(required=True))
    is_swap_completed = graphene.Boolean(
        vehicle_id=graphene.String(required=True),
        shift_id=graphene.String(required=True)
    )
    is_shift_completed = graphene.Boolean(shift_id=graphene.String(required=True))


    def resolve_all_vehicles(self, info, **kwargs):
        return Vehicle.objects.all()

    def resolve_vehicle(self, info, vehicle_id):
        return Vehicle.objects.get(id=vehicle_id)

    def resolve_vehicles_in_shift(self, info, shift_id):
        return get_vehicles_in_shift(shift_id=shift_id)

    def resolve_is_swap_completed(self, info, vehicle_id, shift_id):
        return is_swap_completed(vehicle_id=vehicle_id, shift_id=shift_id)

    def resolve_is_shift_completed(self, info, shift_id):
        return is_shift_completed(shift_id=shift_id)


class CreateShift(graphene.Mutation):
    Output = ShiftType

    def mutate(root, info):
        return create_shift()


class CreateAutomaticShift(graphene.Mutation):
    class Arguments:
        lat = graphene.Float(required=True)
        long = graphene.Float(required=True)

    Output = graphene.List(VehicleType)

    def mutate(root, info, lat: float, long: float):
        return auto_create_shift(lat=lat, long=long)


class AddVehiclesToShift(graphene.Mutation):
    class Arguments:
        vehicle_ids = graphene.List(graphene.NonNull(graphene.String), required=True)
        shift_id = graphene.String(required=True)

    Output = graphene.List(VehicleShiftType)

    def mutate(root, info, vehicle_ids: List[str], shift_id: str):
        return add_vehicles_to_shift(vehicle_ids=vehicle_ids, shift_id=shift_id)


class SwapVehicleBattery(graphene.Mutation):
    class Arguments:
        vehicle_id = graphene.String(required=True)

    Output = VehicleType

    def mutate(root, info, vehicle_id: str):
        return swap_vehicle_battery(vehicle_id=vehicle_id)


class Mutation(graphene.ObjectType):
    create_shift = CreateShift.Field()
    create_automatic_shift = CreateAutomaticShift.Field()
    add_vehicles_to_shift = AddVehiclesToShift.Field()
    swap_vehicle_battery = SwapVehicleBattery.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
