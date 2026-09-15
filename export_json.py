import osmnx as ox
import pandas as pd
import json
from shapely import wkt


# ============================================================
# CONFIGURATION
# ============================================================

LATITUDE = 12.99615
LONGITUDE = 77.71112
RADIUS = 5000

GRAPH_FILE = "whitefield_road_network.graphml"

HOSPITAL_FILE = "whitefield_hospitals.csv"
POLICE_FILE = "whitefield_police.csv"
FIRE_FILE = "whitefield_fire_stations.csv"
SCHOOL_FILE = "whitefield_schools.csv"
POWER_FILE = "whitefield_power_osm.csv"

OUTPUT_FILE = "whitefield_network.json"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_value(value):

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value


def safe_id(value):

    """
    Convert OSM IDs to integers when possible.
    Otherwise keep them as strings.
    """

    try:
        return int(value)
    except Exception:
        return str(value)


def get_facility_location(row):

    """
    Extract latitude and longitude from a CSV row.

    The geometry column contains WKT such as:
        POINT (...)
        POLYGON (...)
    """

    # --------------------------------------------------------
    # First try latitude / longitude columns
    # --------------------------------------------------------

    if (
        "latitude" in row.index
        and "longitude" in row.index
    ):

        lat = clean_value(row["latitude"])
        lon = clean_value(row["longitude"])

        if lat is not None and lon is not None:
            return float(lat), float(lon)


    # --------------------------------------------------------
    # Otherwise parse geometry
    # --------------------------------------------------------

    if "geometry" in row.index:

        geometry_text = row["geometry"]

        if not pd.isna(geometry_text):

            try:

                geometry = wkt.loads(
                    str(geometry_text)
                )

                # Point
                if geometry.geom_type == "Point":

                    return (
                        float(geometry.y),
                        float(geometry.x)
                    )

                # Polygon / LineString / MultiPolygon etc.
                point = geometry.representative_point()

                return (
                    float(point.y),
                    float(point.x)
                )

            except Exception:
                pass


    return None, None


def get_facility_name(row, default_name):

    if "name" not in row.index:
        return default_name

    value = row["name"]

    if pd.isna(value):
        return default_name

    return str(value)


def get_osm_id(row):

    # Depending on how the CSV was generated,
    # this may appear under different names.

    for column in [
        "element id",
        "osmid",
        "osm_id"
    ]:

        if column in row.index:

            value = clean_value(
                row[column]
            )

            if value is not None:
                return safe_id(value)

    return None


# ============================================================
# LOAD ROAD NETWORK
# ============================================================

print("=" * 70)
print("LOADING WHITEFIELD / HOODI ROAD NETWORK")
print("=" * 70)

G = ox.load_graphml(
    GRAPH_FILE
)

print(
    "Road nodes:",
    len(G.nodes)
)

print(
    "Road edges:",
    len(G.edges)
)

print()


# ============================================================
# CREATE ROAD NODES
# ============================================================

print("=" * 70)
print("CREATING ROAD NODE DATA")
print("=" * 70)

network_nodes = []


for node_id, data in G.nodes(
    data=True
):

    x = data.get("x")
    y = data.get("y")

    if x is None or y is None:
        continue

    network_nodes.append({

        "id": safe_id(node_id),

        "latitude": float(y),

        "longitude": float(x),

        "type": "ROAD_NODE"

    })


print(
    "Network nodes created:",
    len(network_nodes)
)

print()


# ============================================================
# CREATE ROAD EDGES
# ============================================================

print("=" * 70)
print("CREATING ROAD EDGE DATA")
print("=" * 70)

roads = []


road_counter = 1


for u, v, key, data in G.edges(
    keys=True,
    data=True
):

    # --------------------------------------------------------
    # Road name
    # --------------------------------------------------------

    name = data.get(
        "name"
    )

    if isinstance(name, list):

        name = ", ".join(
            str(x)
            for x in name
        )

    if name is None:
        name = "Unnamed Road"


    # --------------------------------------------------------
    # Highway type
    # --------------------------------------------------------

    highway = data.get(
        "highway"
    )

    if isinstance(highway, list):

        highway = ", ".join(
            str(x)
            for x in highway
        )

    if highway is None:
        highway = "unknown"


    # --------------------------------------------------------
    # Length
    # --------------------------------------------------------

    length = data.get(
        "length",
        0
    )

    try:
        length = float(length)
    except Exception:
        length = 0.0


    # --------------------------------------------------------
    # One-way
    # --------------------------------------------------------

    oneway = data.get(
        "oneway",
        False
    )

    if isinstance(oneway, str):

        oneway = (
            oneway.lower()
            in [
                "true",
                "yes",
                "1"
            ]
        )

    else:

        oneway = bool(oneway)


    # --------------------------------------------------------
    # Number of lanes
    # --------------------------------------------------------

    lanes = data.get(
        "lanes"
    )

    if isinstance(lanes, list):

        lanes = lanes[0]

    try:

        if lanes is not None:
            lanes = float(lanes)

    except Exception:

        lanes = None


    # --------------------------------------------------------
    # Max speed
    # --------------------------------------------------------

    maxspeed = data.get(
        "maxspeed"
    )

    if isinstance(maxspeed, list):

        maxspeed = ", ".join(
            str(x)
            for x in maxspeed
        )


    # --------------------------------------------------------
    # Geometry
    # --------------------------------------------------------

    geometry = data.get(
        "geometry"
    )

    coordinates = []


    if geometry is not None:

        try:

            coordinates = [

                [
                    float(x),
                    float(y)
                ]

                for x, y
                in geometry.coords

            ]

        except Exception:

            coordinates = []


    # --------------------------------------------------------
    # If geometry is unavailable,
    # use start/end node coordinates
    # --------------------------------------------------------

    if not coordinates:

        start_data = G.nodes[u]
        end_data = G.nodes[v]

        coordinates = [

            [
                float(start_data["x"]),
                float(start_data["y"])
            ],

            [
                float(end_data["x"]),
                float(end_data["y"])
            ]

        ]


    # --------------------------------------------------------
    # Create road object
    # --------------------------------------------------------

    road = {

        "id": road_counter,

        "osm_u": safe_id(u),

        "osm_v": safe_id(v),

        "osm_key": safe_id(key),

        "from_node": safe_id(u),

        "to_node": safe_id(v),

        "name": name,

        "highway": highway,

        "length_m": length,

        "lanes": lanes,

        "maxspeed": maxspeed,

        "oneway": oneway,

        "type": "ROAD",

        # ----------------------------------------------------
        # Simulation values
        #
        # These are INITIAL PLACEHOLDERS.
        # We will calibrate them later.
        # ----------------------------------------------------

        "capacity": 100.0,

        "load": 50.0,

        "originalLoad": 50.0,

        "priority": 3,

        "status": "WORKING",

        "availability": 100.0,

        "populationServed": 0,

        "repairRemaining": 0,

        "directFailure": False,

        "displacedLoad": 0.0,

        # ----------------------------------------------------
        # GeoJSON-style coordinates
        #
        # [longitude, latitude]
        # ----------------------------------------------------

        "geometry": coordinates

    }


    roads.append(
        road
    )


    road_counter += 1


print(
    "Road edges created:",
    len(roads)
)

print()


# ============================================================
# FIND NEAREST ROAD NODE
# ============================================================

def find_nearest_road_node(
    latitude,
    longitude
):

    if latitude is None or longitude is None:
        return None

    try:

        nearest = ox.distance.nearest_nodes(
            G,
            X=float(longitude),
            Y=float(latitude)
        )

        return safe_id(nearest)

    except Exception:

        return None


# ============================================================
# LOAD FACILITIES
# ============================================================

def load_facilities(
    filename,
    facility_type
):

    print(
        f"Loading {facility_type}..."
    )

    try:

        df = pd.read_csv(
            filename,
            encoding="latin-1"
        )

    except Exception as e:

        print(
            f"Could not load {filename}"
        )

        print(e)

        return []


    facilities = []


    for index, row in df.iterrows():

        latitude, longitude = \
            get_facility_location(row)


        name = get_facility_name(
            row,
            f"Unnamed {facility_type}"
        )


        osm_id = get_osm_id(
            row
        )


        nearest_node = \
            find_nearest_road_node(
                latitude,
                longitude
            )


        component = {

            "id":
                f"{facility_type}_{index + 1}",

            "osm_id":
                osm_id,

            "name":
                name,

            "type":
                facility_type,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "nearest_road_node":
                nearest_node,

            # ------------------------------------------------
            # Simulation placeholders
            # ------------------------------------------------

            "capacity":
                100.0,

            "load":
                50.0,

            "originalLoad":
                50.0,

            "priority":
                5,

            "status":
                "WORKING",

            "availability":
                100.0,

            "populationServed":
                0,

            "repairRemaining":
                0,

            "directFailure":
                False,

            "displacedLoad":
                0.0

        }


        facilities.append(
            component
        )


    print(
        facility_type,
        ":",
        len(facilities)
    )

    print()


    return facilities


# ============================================================
# LOAD HOSPITALS
# ============================================================

hospitals = load_facilities(
    HOSPITAL_FILE,
    "HOSPITAL"
)


# ============================================================
# LOAD POLICE
# ============================================================

police = load_facilities(
    POLICE_FILE,
    "POLICE_STATION"
)


# ============================================================
# LOAD FIRE STATIONS
# ============================================================

fire_stations = load_facilities(
    FIRE_FILE,
    "FIRE_STATION"
)


# ============================================================
# LOAD SCHOOLS
# ============================================================

schools = load_facilities(
    SCHOOL_FILE,
    "SCHOOL"
)


# ============================================================
# LOAD OSM POWER
# ============================================================

power = load_facilities(
    POWER_FILE,
    "POWER_INFRASTRUCTURE"
)


# ============================================================
# ADD HOODY POWER RECEIVING STATION
# ============================================================

print("=" * 70)
print("ADDING HOODY POWER RECEIVING STATION")
print("=" * 70)


hoody_lat = 12.9961479
hoody_lon = 77.7111237


hoody_nearest_node = \
    find_nearest_road_node(
        hoody_lat,
        hoody_lon
    )


hoody_power = {

    "id":
        "POWER_HOODY_001",

    "osm_id":
        None,

    "name":
        "Hoody Power Receiving Station, KPTCL",

    "type":
        "POWER_STATION",

    "latitude":
        hoody_lat,

    "longitude":
        hoody_lon,

    "nearest_road_node":
        hoody_nearest_node,

    # --------------------------------------------------------
    # IMPORTANT SIMULATION VALUES
    # --------------------------------------------------------

    "capacity":
        500.0,

    "load":
        350.0,

    "originalLoad":
        350.0,

    "priority":
        5,

    "status":
        "WORKING",

    "availability":
        100.0,

    "populationServed":
        50000,

    "repairRemaining":
        0,

    "directFailure":
        False,

    "displacedLoad":
        0.0

}


print(
    "Name:",
    hoody_power["name"]
)

print(
    "Latitude:",
    hoody_power["latitude"]
)

print(
    "Longitude:",
    hoody_power["longitude"]
)

print(
    "Nearest road node:",
    hoody_power["nearest_road_node"]
)

print()


# ============================================================
# CREATE MASTER JSON
# ============================================================

print("=" * 70)
print("CREATING MASTER JSON")
print("=" * 70)


network = {

    "metadata": {

        "project":
            "Whitefield Cascading Failure Simulator",

        "city":
            "Bengaluru",

        "study_area":
            "Whitefield / Hoodi",

        "center": {

            "latitude":
                LATITUDE,

            "longitude":
                LONGITUDE

        },

        "radius_m":
            RADIUS,

        "coordinate_system":
            "WGS84",

        "data_source":
            "OpenStreetMap",

        "simulation_engine":
            "C++",

        "version":
            "1.0"

    },


    # ========================================================
    # ROAD NETWORK
    # ========================================================

    "road_network": {

        "nodes":
            network_nodes,

        "edges":
            roads

    },


    # ========================================================
    # FACILITIES
    # ========================================================

    "facilities": {

        "hospitals":
            hospitals,

        "police_stations":
            police,

        "fire_stations":
            fire_stations,

        "schools":
            schools,

        "power_infrastructure":
            power,

        "critical_power_station":
            hoody_power

    }

}


# ============================================================
# SAVE JSON
# ============================================================

print(
    "Saving:",
    OUTPUT_FILE
)


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        network,
        file,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("JSON CREATED SUCCESSFULLY")
print("=" * 70)

print(
    "Road nodes:",
    len(network_nodes)
)

print(
    "Road edges:",
    len(roads)
)

print(
    "Hospitals:",
    len(hospitals)
)

print(
    "Police stations:",
    len(police)
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
    "OSM power infrastructure:",
    len(power)
)

print(
    "Hoody power station:",
    1
)

print()

print(
    "Output file:",
    OUTPUT_FILE
)

print("=" * 70)
print("DONE")
print("=" * 70)