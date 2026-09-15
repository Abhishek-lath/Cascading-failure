import json
import math


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "whitefield_network.json"
OUTPUT_FILE = "dependency_graph.json"


# Maximum distance at which a facility can be considered
# dependent on a power infrastructure node.
#
# These are SIMULATION assumptions, not real electrical
# supply boundaries.
#
# We will explain this in the presentation.

POWER_DEPENDENCY_RADIUS = {

    "HOSPITAL": 3000,

    "POLICE_STATION": 3000,

    "FIRE_STATION": 3000,

    "SCHOOL": 2500,

    "POWER_INFRASTRUCTURE": 2000

}


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371000  # Earth radius in metres

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(
        lat2 - lat1
    )

    dlambda = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(dphi / 2) ** 2
        +
        math.cos(phi1)
        *
        math.cos(phi2)
        *
        math.sin(dlambda / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# ============================================================
# LOAD JSON
# ============================================================

print("=" * 70)
print("LOADING WHITEFIELD NETWORK")
print("=" * 70)


with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as f:

    network = json.load(f)


print("JSON loaded successfully.")
print()


# ============================================================
# EXTRACT FACILITIES
# ============================================================

facilities_data = network["facilities"]


hospitals = facilities_data[
    "hospitals"
]


police_stations = facilities_data[
    "police_stations"
]


fire_stations = facilities_data[
    "fire_stations"
]


schools = facilities_data[
    "schools"
]


power_infrastructure = facilities_data[
    "power_infrastructure"
]


critical_power = facilities_data[
    "critical_power_station"
]


# ============================================================
# COMBINE NON-POWER FACILITIES
# ============================================================

all_facilities = (

    hospitals
    + police_stations
    + fire_stations
    + schools

)


print("=" * 70)
print("FACILITY COUNTS")
print("=" * 70)


print(
    "Hospitals:",
    len(hospitals)
)

print(
    "Police stations:",
    len(police_stations)
)

print(
    "Fire stations:",
    len(fire_stations)
)

print(
    "Schools:",
    len(schools)
)

print(
    "Power infrastructure:",
    len(power_infrastructure)
)

print()


# ============================================================
# POWER SOURCES
# ============================================================

# Add the special Hoody power station to the list of
# possible simulated power sources.

power_sources = []


for p in power_infrastructure:

    if (
        p.get("latitude") is None
        or
        p.get("longitude") is None
    ):
        continue


    power_sources.append({

        "id":
            p["id"],

        "name":
            p["name"],

        "type":
            p["type"],

        "latitude":
            p["latitude"],

        "longitude":
            p["longitude"],

        "capacity":
            p.get("capacity", 100.0),

        "source":
            "OSM"

    })


# Add Hoody station

if (
    critical_power.get("latitude") is not None
    and
    critical_power.get("longitude") is not None
):

    power_sources.append({

        "id":
            critical_power["id"],

        "name":
            critical_power["name"],

        "type":
            critical_power["type"],

        "latitude":
            critical_power["latitude"],

        "longitude":
            critical_power["longitude"],

        "capacity":
            critical_power.get(
                "capacity",
                500.0
            ),

        "source":
            "PROJECT_CRITICAL_ASSET"

    })


print(
    "Total simulated power sources:",
    len(power_sources)
)

print()


# ============================================================
# FIND NEAREST POWER SOURCE
# ============================================================

def find_nearest_power(
    facility
):

    lat = facility.get(
        "latitude"
    )

    lon = facility.get(
        "longitude"
    )


    if lat is None or lon is None:
        return None


    nearest = None

    nearest_distance = float(
        "inf"
    )


    for power in power_sources:

        distance = haversine(

            float(lat),
            float(lon),

            float(power["latitude"]),
            float(power["longitude"])

        )


        if distance < nearest_distance:

            nearest_distance = distance

            nearest = power


    if nearest is None:
        return None


    return {

        "power_id":
            nearest["id"],

        "power_name":
            nearest["name"],

        "distance_m":
            round(
                nearest_distance,
                2
            )

    }


# ============================================================
# CREATE DEPENDENCY EDGES
# ============================================================

print("=" * 70)
print("BUILDING DEPENDENCY GRAPH")
print("=" * 70)


dependencies = []


# ------------------------------------------------------------
# POWER → FACILITY
# ------------------------------------------------------------

for facility in all_facilities:

    facility_type = facility[
        "type"
    ]


    nearest = find_nearest_power(
        facility
    )


    if nearest is None:
        continue


    distance = nearest[
        "distance_m"
    ]


    radius = POWER_DEPENDENCY_RADIUS.get(
        facility_type,
        2500
    )


    # Only create dependency if within
    # our simulation radius.

    if distance <= radius:

        # ----------------------------------------------------
        # Dependency strength
        #
        # Closer = stronger dependency
        # ----------------------------------------------------

        strength = max(
            0.1,
            1.0 - (
                distance / radius
            )
        )


        # ----------------------------------------------------
        # Criticality
        # ----------------------------------------------------

        criticality = {

            "HOSPITAL": 1.0,

            "FIRE_STATION": 1.0,

            "POLICE_STATION": 0.9,

            "SCHOOL": 0.5

        }.get(
            facility_type,
            0.5
        )


        dependencies.append({

            "from":
                nearest["power_id"],

            "to":
                facility["id"],

            "type":
                "POWER_DEPENDENCY",

            "distance_m":
                distance,

            "strength":
                round(
                    strength,
                    3
                ),

            "criticality":
                criticality,

            "failure_threshold":
                round(
                    0.35
                    + (
                        strength
                        * 0.4
                    ),
                    3
                )

        })


# ============================================================
# POWER → POWER INFRASTRUCTURE
# ============================================================

for facility in power_infrastructure:

    lat = facility.get(
        "latitude"
    )

    lon = facility.get(
        "longitude"
    )


    if lat is None or lon is None:
        continue


    nearest = None

    nearest_distance = float(
        "inf"
    )


    for power in power_sources:

        if power["id"] == facility["id"]:
            continue


        distance = haversine(

            float(lat),
            float(lon),

            float(power["latitude"]),
            float(power["longitude"])

        )


        if distance < nearest_distance:

            nearest_distance = distance

            nearest = power


    if nearest is None:
        continue


    if nearest_distance <= 2000:

        dependencies.append({

            "from":
                nearest["id"],

            "to":
                facility["id"],

            "type":
                "POWER_NETWORK_DEPENDENCY",

            "distance_m":
                round(
                    nearest_distance,
                    2
                ),

            "strength":
                round(
                    max(
                        0.1,
                        1.0
                        -
                        (
                            nearest_distance
                            / 2000
                        )
                    ),
                    3
                ),

            "criticality":
                1.0,

            "failure_threshold":
                0.6

        })


# ============================================================
# FACILITY → ROAD
# ============================================================

facility_road_links = []


for facility in all_facilities:

    road_node = facility.get(
        "nearest_road_node"
    )


    if road_node is None:
        continue


    facility_road_links.append({

        "facility_id":
            facility["id"],

        "road_node":
            road_node,

        "type":
            "ROAD_ACCESS"

    })


# ============================================================
# CRITICAL POWER → ROAD
# ============================================================

critical_power_road = {

    "facility_id":
        critical_power["id"],

    "road_node":
        critical_power.get(
            "nearest_road_node"
        ),

    "type":
        "POWER_ROAD_ACCESS"

}


# ============================================================
# CREATE DEPENDENCY GRAPH
# ============================================================

dependency_graph = {

    "metadata": {

        "project":
            "Whitefield Cascading Failure Simulator",

        "description":
            "Simulation dependency graph generated from "
            "OpenStreetMap spatial data",

        "dependency_method":
            "Geographical proximity and criticality",

        "warning":
            "Dependencies represent simulation assumptions "
            "and do not claim actual electrical supply relationships."

    },


    "power_sources":
        power_sources,


    "dependencies":
        dependencies,


    "facility_road_links":
        facility_road_links,


    "critical_power_road":
        critical_power_road

}


# ============================================================
# SAVE
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        dependency_graph,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("DEPENDENCY GRAPH CREATED")
print("=" * 70)


print(
    "Power sources:",
    len(power_sources)
)

print(
    "Power dependencies:",
    len(dependencies)
)

print(
    "Facility → road links:",
    len(facility_road_links)
)

print()


# ------------------------------------------------------------
# Dependency breakdown
# ------------------------------------------------------------

power_dependency_count = sum(

    1

    for d in dependencies

    if d["type"] == "POWER_DEPENDENCY"

)


power_network_count = sum(

    1

    for d in dependencies

    if d["type"]
    == "POWER_NETWORK_DEPENDENCY"

)


print(
    "Power → facility:",
    power_dependency_count
)

print(
    "Power → power:",
    power_network_count
)

print()


# ============================================================
# SHOW HOODY IMPACT
# ============================================================

print("=" * 70)
print("HOODY POWER STATION DEPENDENCIES")
print("=" * 70)


hoody_id = critical_power[
    "id"
]


hoody_dependencies = [

    d

    for d in dependencies

    if d["from"] == hoody_id

]


print(
    "Hoody power station:",
    critical_power["name"]
)

print(
    "Direct simulated dependencies:",
    len(hoody_dependencies)
)

print()


for d in hoody_dependencies[:20]:

    print(

        "→",

        d["to"],

        "| distance:",

        d["distance_m"],

        "m",

        "| strength:",

        d["strength"]

    )


if len(hoody_dependencies) > 20:

    print(
        "... and",
        len(hoody_dependencies) - 20,
        "more"
    )


print()


print("=" * 70)
print("DONE")
print("=" * 70)