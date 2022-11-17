import uuid
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point


def uuid_str():
    return str(uuid.uuid4())


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created' and 'modified' fields.
    """

    id = models.CharField(
        primary_key=True, max_length=128, default=uuid_str, editable=False
    )
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Vehicle(TimeStampedModel):
    license_plate = models.CharField(max_length=80, unique=True, null=False)
    battery_level = models.FloatField(null=False)
    in_use = models.BooleanField(default=False, null=False)
    model = models.CharField(max_length=10, null=False)
    # srid = spatial reference identifier - specifies geographic coords
    location = models.PointField(geography=True, srid=4326)
    location_lat = models.FloatField(null=False)
    location_long = models.FloatField(null=False)

    def save(self, **kwargs):
        self.location = Point(self.location_long, self.location_lat)
        super(Vehicle, self).save(**kwargs)

    def __str__(self):
        return f"{self.license_plate}"


class Shift(TimeStampedModel):
    completed = models.BooleanField(default=False, null=False)
    active = models.BooleanField(default=True, null=False)


class VehicleShift(TimeStampedModel):
    vehicle = models.ForeignKey(Vehicle, related_name="vehicle_shift", on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, related_name="vehicle_shift", on_delete=models.CASCADE)
    swap_completed = models.BooleanField(default=False, null=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vehicle", "shift"], name="unique_vehicle_shift"
            )
        ]

    def __str__(self):
        return f"{self.vehicle}: swap {'completed' if self.swap_completed else 'not completed'}"

