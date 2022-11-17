## Vehicle Shift Manager

To run: 

First, set up a postgres db instance configured with the settings defined
in settings.py

Activate virtual environment and install all requirements from requirements.txt:
```
source venv/bin/activate
pip install -r requirements.txt 
```

Ensure you have the correct settings module defined by running:
``` 
export DJANGO_SETTINGS_MODULE=config.settings
```
Then, to run the server and open up the graphql explorer:
```
python manage.py runserver
```
You can access the API at: http://127.0.0.1:8000/api/graphql



## API Guide: 
1. Convenience query to get all vehicles
``` gql
query allVehicles {
  allVehicles {
    batteryLevel
    id
    inUse
    licensePlate
    locationLat
    locationLong
    model
  }
}
```

2. Review all vehicles in a shift
``` gql
query vis {
  vehiclesInShift(shiftId: "") {
    licensePlate
  }
}
```

3. Check if a swap has been completed for any vehicle in a shift.
``` gql
query swapCompleted {
  isSwapCompleted(shiftId: "", vehicleId: "")
}
```

4. Check if all vehicles in the shift have had their battery swaps
completed.
``` gql
query shiftCompleted {
  isShiftCompleted(shiftId: "")
}
```

5. Complete a battery swap for a vehicle. Note: we are assuming 
that we have an infinite supply of batteries charged to 100%.
``` gql
mutation swapBattery {
  swapVehicleBattery(vehicleId: "") {
    batteryLevel
  }
}
```

6. Create a shift
``` gql
mutation createShift {
  createShift {
    id
    completed
    active
  }
}
```

7. Add Vehicles to a shift
``` gql
mutation addV {
  addVehiclesToShift(shiftId: "" vehicleIds: [""]) {
    swapCompleted
    id
  }
}
```

8. Create a shift automatically. The suggested long lat provided correspond to a 
location in Dumbo, Brooklyn. Assuming that we don't want to have vehicles in the shift
be more than 50 miles away from current location. Distance is represented in miles.
``` gql
mutation createAutoShift {
  createAutomaticShift(long: -73.992226, lat: 40.694891) {
    vehicleShift {
      swapCompleted
    }
    batteryLevel
    licensePlate
    distance
  }
}

```