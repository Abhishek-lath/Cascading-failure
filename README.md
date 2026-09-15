# Whitefield Cascading Failure Simulator

An OpenStreetMap-based infrastructure resilience demo for Whitefield, Bengaluru.

The simulator visualizes roads, hospitals, schools, police stations, fire stations, power infrastructure, and a critical Hoody power receiving station. It animates cascading failures, affected roads, live metrics, and a cascade timeline.

## Live Demo

After GitHub Pages is enabled, the site will be available at:

```text
https://YOUR_GITHUB_USERNAME.github.io/whitefield-cascading-failure-simulator/
```

## Features

- Real OpenStreetMap-derived Whitefield road network
- 44k+ road segments rendered in Leaflet
- Infrastructure markers for hospitals, police, fire, schools, and power assets
- Hoody Power Receiving Station default cascade scenario
- Right-click any facility marker to start a custom cascade from that building
- Live cascade timeline
- Failed infrastructure and affected roads highlighted on the map
- Dashboard metrics and severity score

## Run Locally

Keep these files in the same folder:

```text
index.html
whitefield_network.json
simulation_output.json
```

Start a local server:

```powershell
python -m http.server 8000
```

Open:

```text
http://localhost:8000
```

## Demo Flow

1. Open the live demo.
2. Press **START CASCADE** to run the default Hoody power failure scenario.
3. Press **RESET**.
4. Right-click another infrastructure marker, such as a fire station or hospital.
5. Press **START CASCADE** again to show a custom what-if scenario.

## Notes

The demo loads a large real-world road network JSON file, so the initial map load can take a few seconds.

Dependencies are loaded via CDN and no Java or C++ runtime is required for the frontend demo.