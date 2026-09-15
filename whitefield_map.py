import osmnx as ox
import folium
import pandas as pd
import json


# ============================================================
# 1. WHITEFIELD / HOODI CENTER
# ============================================================

latitude = 12.99615
longitude = 77.71112
dist = 5000


print("=" * 60)
print("WHITEFIELD / HOODI INTERACTIVE MAP")
print("=" * 60)


# ============================================================
# 2. DOWNLOAD ROAD NETWORK
# ============================================================

print("Downloading road network...")

G = ox.graph_from_point(
    (latitude, longitude),
    dist=dist,
    network_type="drive"
)

nodes, edges = ox.graph_to_gdfs(G)

print(f"Road nodes : {len(nodes)}")
print(f"Road edges : {len(edges)}")
print()


# ============================================================
# 3. DOWNLOAD HOSPITALS, POLICE, FIRE, SCHOOLS
# ============================================================

print("Downloading facilities...")

amenities = ox.features_from_point(
    (latitude, longitude),
    tags={
        "amenity": [
            "hospital",
            "police",
            "fire_station",
            "school"
        ]
    },
    dist=dist
)

print(f"Total facilities: {len(amenities)}")
print()


# ============================================================
# 4. SEPARATE FACILITIES
# ============================================================

hospitals = amenities[
    amenities["amenity"] == "hospital"
].copy()

police = amenities[
    amenities["amenity"] == "police"
].copy()

fire_stations = amenities[
    amenities["amenity"] == "fire_station"
].copy()

schools = amenities[
    amenities["amenity"] == "school"
].copy()


print("Hospitals      :", len(hospitals))
print("Police stations:", len(police))
print("Fire stations  :", len(fire_stations))
print("Schools        :", len(schools))
print()


# ============================================================
# 5. DOWNLOAD POWER INFRASTRUCTURE
# ============================================================

print("Downloading power infrastructure...")

power = ox.features_from_point(
    (latitude, longitude),
    tags={
        "power": [
            "substation",
            "transformer",
            "plant",
            "generator"
        ]
    },
    dist=dist
)

print("Power features :", len(power))
print()


# ============================================================
# 6. CREATE LEAFLET MAP
# ============================================================

m = folium.Map(
    location=[latitude, longitude],
    zoom_start=13,
    tiles="OpenStreetMap",
    control_scale=True
)


# ============================================================
# 7. ROAD NETWORK LAYER
# ============================================================

road_layer = folium.FeatureGroup(
    name="🛣️ Road Network",
    show=True
)


# Convert road GeoDataFrame to GeoJSON
road_geojson = json.loads(
    edges.to_json()
)


folium.GeoJson(
    road_geojson,
    name="Roads",
    style_function=lambda feature: {
        "color": "#3388ff",
        "weight": 1,
        "opacity": 0.7
    }
).add_to(road_layer)


road_layer.add_to(m)


# ============================================================
# 8. FUNCTION TO GET A POINT FROM A FACILITY
# ============================================================

def get_location(row):

    geometry = row.geometry

    if geometry.geom_type == "Point":

        return geometry.y, geometry.x

    else:

        point = geometry.representative_point()

        return point.y, point.x


# ============================================================
# 9. HOSPITAL LAYER
# ============================================================

hospital_layer = folium.FeatureGroup(
    name="🏥 Hospitals",
    show=True
)


for _, row in hospitals.iterrows():

    lat, lon = get_location(row)

    name = row.get("name", "Unnamed Hospital")

    if pd.isna(name):
        name = "Unnamed Hospital"

    folium.Marker(
        location=[lat, lon],

        popup=folium.Popup(
            f"""
            <b>🏥 Hospital</b><br>
            {name}
            """,
            max_width=300
        ),

        tooltip=str(name),

        icon=folium.Icon(
            color="red",
            icon="plus",
            prefix="fa"
        )

    ).add_to(hospital_layer)


hospital_layer.add_to(m)


# ============================================================
# 10. POLICE LAYER
# ============================================================

police_layer = folium.FeatureGroup(
    name="👮 Police Stations",
    show=True
)


for _, row in police.iterrows():

    lat, lon = get_location(row)

    name = row.get("name", "Unnamed Police Station")

    if pd.isna(name):
        name = "Unnamed Police Station"

    folium.Marker(
        location=[lat, lon],

        popup=folium.Popup(
            f"""
            <b>👮 Police Station</b><br>
            {name}
            """,
            max_width=300
        ),

        tooltip=str(name),

        icon=folium.Icon(
            color="blue",
            icon="shield",
            prefix="fa"
        )

    ).add_to(police_layer)


police_layer.add_to(m)


# ============================================================
# 11. FIRE STATION LAYER
# ============================================================

fire_layer = folium.FeatureGroup(
    name="🚒 Fire Stations",
    show=True
)


for _, row in fire_stations.iterrows():

    lat, lon = get_location(row)

    name = row.get("name", "Unnamed Fire Station")

    if pd.isna(name):
        name = "Unnamed Fire Station"

    folium.Marker(
        location=[lat, lon],

        popup=folium.Popup(
            f"""
            <b>🚒 Fire Station</b><br>
            {name}
            """,
            max_width=300
        ),

        tooltip=str(name),

        icon=folium.Icon(
            color="orange",
            icon="fire-extinguisher",
            prefix="fa"
        )

    ).add_to(fire_layer)


fire_layer.add_to(m)


# ============================================================
# 12. SCHOOL LAYER
# ============================================================

school_layer = folium.FeatureGroup(
    name="🏫 Schools",
    show=False
)


for _, row in schools.iterrows():

    lat, lon = get_location(row)

    name = row.get("name", "Unnamed School")

    if pd.isna(name):
        name = "Unnamed School"

    folium.CircleMarker(
        location=[lat, lon],

        radius=4,

        popup=folium.Popup(
            f"""
            <b>🏫 School</b><br>
            {name}
            """,
            max_width=300
        ),

        tooltip=str(name),

        color="green",
        fill=True,
        fill_color="green",
        fill_opacity=0.8

    ).add_to(school_layer)


school_layer.add_to(m)


# ============================================================
# 13. POWER INFRASTRUCTURE LAYER
# ============================================================

power_layer = folium.FeatureGroup(
    name="⚡ OSM Power Infrastructure",
    show=True
)


for _, row in power.iterrows():

    lat, lon = get_location(row)

    name = row.get("name", "Unnamed Power Infrastructure")

    power_type = row.get("power", "Unknown")

    if pd.isna(name):
        name = "Unnamed Power Infrastructure"

    if pd.isna(power_type):
        power_type = "Unknown"

    folium.Marker(
        location=[lat, lon],

        popup=folium.Popup(
            f"""
            <b>⚡ Power Infrastructure</b><br>
            <b>Name:</b> {name}<br>
            <b>Type:</b> {power_type}
            """,
            max_width=350
        ),

        tooltip=f"⚡ {name}",

        icon=folium.Icon(
            color="purple",
            icon="bolt",
            prefix="fa"
        )

    ).add_to(power_layer)


power_layer.add_to(m)


# ============================================================
# 14. HOODY POWER RECEIVING STATION
# ============================================================

# Verified coordinates from the Google Maps location
hoody_lat = 12.9961479
hoody_lon = 77.7111237


hoody_layer = folium.FeatureGroup(
    name="⚡ Hoody Power Receiving Station",
    show=True
)


folium.Marker(
    location=[hoody_lat, hoody_lon],

    popup=folium.Popup(
        """
        <div style="font-size: 14px;">

        <h4>⚡ Hoody Power Receiving Station</h4>

        <b>Organization:</b> KPTCL<br>

        <b>Location:</b> Hoodi, Whitefield, Bengaluru<br>

        <b>Role:</b> Critical Power Infrastructure<br><br>

        <b>Simulation status:</b>
        <span style="color: green;">
        NORMAL
        </span>

        </div>
        """,

        max_width=400
    ),

    tooltip="⚡ Hoody Power Receiving Station",

    icon=folium.Icon(
        color="darkred",
        icon="bolt",
        prefix="fa"
    )

).add_to(hoody_layer)


hoody_layer.add_to(m)


# ============================================================
# 15. ADD STUDY AREA CIRCLE
# ============================================================

study_area_layer = folium.FeatureGroup(
    name="Study Area (5 km)",
    show=False
)


folium.Circle(
    location=[latitude, longitude],

    radius=dist,

    color="black",

    fill=False,

    weight=2,

    dash_array="5, 5",

    popup="Whitefield/Hoodi 5 km study area"

).add_to(study_area_layer)


study_area_layer.add_to(m)


# ============================================================
# 16. ADD LAYER CONTROL
# ============================================================

folium.LayerControl(
    collapsed=False
).add_to(m)


# ============================================================
# 17. ADD TITLE
# ============================================================

title_html = """

<div style="
position: fixed;
top: 10px;
left: 50%;
transform: translateX(-50%);
z-index: 9999;
background-color: white;
padding: 10px 20px;
border-radius: 8px;
box-shadow: 0px 2px 8px rgba(0,0,0,0.3);
font-size: 20px;
font-weight: bold;
">

WHITEFIELD / HOODI
<br>

<span style="
font-size: 13px;
font-weight: normal;
">

Cascading Failure Study Area

</span>

</div>

"""

m.get_root().html.add_child(
    folium.Element(title_html)
)


# ============================================================
# 18. SAVE MAP
# ============================================================

output_file = "whitefield_map.html"

m.save(output_file)


print("=" * 60)
print("MAP CREATED SUCCESSFULLY")
print("=" * 60)

print(f"File: {output_file}")
print()

print("Open this file in Chrome:")
print(output_file)