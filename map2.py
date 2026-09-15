import osmnx as ox
import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# 1. WHITEFIELD / HOODI CENTER
# ============================================================

latitude = 12.99615
longitude = 77.71112

# Radius in metres
dist = 5000

print("=" * 60)
print("WHITEFIELD / HOODI INFRASTRUCTURE EXTRACTION")
print("=" * 60)

print(f"Center latitude  : {latitude}")
print(f"Center longitude : {longitude}")
print(f"Radius           : {dist} metres")
print()


# ============================================================
# 2. DOWNLOAD ROAD NETWORK
# ============================================================

print("Downloading road network...")

G = ox.graph_from_point(
    (latitude, longitude),
    dist=dist,
    network_type="drive"
)

print("Road network downloaded.")
print(f"Number of road nodes : {len(G.nodes)}")
print(f"Number of road edges : {len(G.edges)}")
print()


# ============================================================
# 3. CONVERT ROAD NETWORK TO GEODATAFRAMES
# ============================================================

nodes, edges = ox.graph_to_gdfs(G)


# ============================================================
# 4. GET HOSPITALS, POLICE, FIRE STATIONS AND SCHOOLS
# ============================================================

print("Downloading hospitals, police stations, fire stations and schools...")

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

print(f"Total amenities found: {len(amenities)}")
print()


# ============================================================
# 5. SHOW AMENITY COUNTS
# ============================================================

print("=" * 60)
print("AMENITY COUNTS")
print("=" * 60)

print(
    amenities["amenity"]
    .value_counts()
    .to_string()
)

print()


# ============================================================
# 6. SEPARATE EACH TYPE
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


# ============================================================
# 7. DOWNLOAD POWER INFRASTRUCTURE SEPARATELY
# ============================================================

print("=" * 60)
print("DOWNLOADING POWER INFRASTRUCTURE")
print("=" * 60)

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

print(f"Power infrastructure found: {len(power)}")
print()


# ============================================================
# 8. SHOW POWER INFRASTRUCTURE
# ============================================================

if len(power) > 0:

    print("POWER TYPES")
    print("-" * 60)

    print(
        power["power"]
        .value_counts()
        .to_string()
    )

    print()

    print("POWER INFRASTRUCTURE DETAILS")
    print("-" * 60)

    columns = [
        column
        for column in ["name", "power", "geometry"]
        if column in power.columns
    ]

    print(
        power[columns].to_string()
    )

else:

    print("No power infrastructure found by OSM.")
    print()


# ============================================================
# 9. SEARCH FOR HOODY / HOODI / KPTCL
# ============================================================

print("=" * 60)
print("SEARCHING FOR HOODY POWER RECEIVING STATION")
print("=" * 60)

if len(power) > 0:

    # Convert name column to strings
    power_names = power["name"].fillna("").astype(str)

    hoody_matches = power[
        power_names.str.contains(
            "hoody|hoodi|kptcl|receiving",
            case=False,
            regex=True
        )
    ].copy()

    if len(hoody_matches) > 0:

        print("Possible matching power infrastructure:")
        print()

        columns = [
            column
            for column in ["name", "power", "geometry"]
            if column in hoody_matches.columns
        ]

        print(
            hoody_matches[columns].to_string()
        )

    else:

        print("OSM did NOT find Hoody Power Receiving Station.")
        print("We will add the verified location manually.")
        print()

else:

    print("OSM has no power infrastructure in this query.")
    print("We will add the Hoody Power Receiving Station manually.")
    print()


# ============================================================
# 10. ADD HOODY POWER RECEIVING STATION
# ============================================================

# Coordinates from the Google Maps location you provided

hoody_power = pd.DataFrame([
    {
        "name": "Hoody Power Receiving Station, KPTCL",
        "type": "power_receiving_station",
        "latitude": 12.9961479,
        "longitude": 77.7111237
    }
])

print("=" * 60)
print("HOODY POWER RECEIVING STATION")
print("=" * 60)

print(hoody_power.to_string(index=False))
print()


# ============================================================
# 11. DISPLAY FACILITY COUNTS
# ============================================================

print("=" * 60)
print("FINAL FACILITY SUMMARY")
print("=" * 60)

print(f"Hospitals       : {len(hospitals)}")
print(f"Police stations : {len(police)}")
print(f"Fire stations   : {len(fire_stations)}")
print(f"Schools         : {len(schools)}")
print(f"OSM power items : {len(power)}")
print(f"Hoody power     : 1")
print()


# ============================================================
# 12. SAVE RAW DATA TO CSV
# ============================================================

amenities.to_csv(
    "whitefield_amenities.csv",
    index=True
)

power.to_csv(
    "whitefield_power_osm.csv",
    index=True
)

hospitals.to_csv(
    "whitefield_hospitals.csv",
    index=True
)

police.to_csv(
    "whitefield_police.csv",
    index=True
)

fire_stations.to_csv(
    "whitefield_fire_stations.csv",
    index=True
)

schools.to_csv(
    "whitefield_schools.csv",
    index=True
)

hoody_power.to_csv(
    "hoody_power_station.csv",
    index=False
)

print("CSV files saved.")
print()


# ============================================================
# 13. SAVE ROAD NETWORK
# ============================================================

ox.save_graphml(
    G,
    filepath="whitefield_road_network.graphml"
)

print("Road network saved as:")
print("whitefield_road_network.graphml")
print()


# ============================================================
# 14. CREATE CLEAN ROAD MAP
# ============================================================

print("Creating clean road map...")

fig, ax = plt.subplots(
    figsize=(14, 14)
)

# Plot ALL roads
edges.plot(
    ax=ax,
    linewidth=0.35,
    color="blue",
    alpha=0.8
)

# Remove axes
ax.set_axis_off()

# White background
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# Save image
plt.savefig(
    "whitefield_detailed_roads.png",
    dpi=300,
    bbox_inches="tight",
    pad_inches=0,
    facecolor="white"
)

plt.show()

print()
print("=" * 60)
print("DONE!")
print("=" * 60)