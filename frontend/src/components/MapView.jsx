import { useEffect, useState } from "react";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "leaflet-defaulticon-compatibility";
import "leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css";

import { getCoordinates } from "../services/api";


function MapController({
  sourcePosition,
  destinationPosition,
  routes,
}) {
  const map = useMap();

  useEffect(() => {
    const points = [];

    if (sourcePosition) {
      points.push(sourcePosition);
    }

    if (destinationPosition) {
      points.push(destinationPosition);
    }

    routes.forEach((route) => {
      if (route.geometry) {
        route.geometry.forEach((point) => {
          points.push(point);
        });
      }
    });

    if (points.length >= 2) {
      map.fitBounds(points, {
        padding: [40, 40],
        maxZoom: 14,
      });
    }
  }, [
    sourcePosition,
    destinationPosition,
    routes,
    map,
  ]);

  return null;
}


function MapView({
  source,
  destination,
  result,
}) {
  const [sourcePosition, setSourcePosition] =
    useState(null);

  const [destinationPosition, setDestinationPosition] =
    useState(null);


  /*
   * Load source and destination coordinates
   */

  useEffect(() => {
    async function loadCoordinates() {
      try {
        if (source) {
          const data =
            await getCoordinates(source);

          setSourcePosition([
            data.lat,
            data.lon,
          ]);
        }

        if (destination) {
          const data =
            await getCoordinates(destination);

          setDestinationPosition([
            data.lat,
            data.lon,
          ]);
        }
      } catch (error) {
        console.log(
          "Coordinate error:",
          error
        );
      }
    }

    loadCoordinates();
  }, [
    source,
    destination,
  ]);


  /*
   * Routes returned by backend
   */

  const routes =
    result?.routes || [];


  /*
   * Decide route color using
   * ML risk prediction.
   */

  function getRouteColor(route) {

    if (route.risk_level === "Unsafe") {
      return "red";
    }

    if (route.risk_level === "Moderate") {
      return "orange";
    }

    if (route.route_type === "Safest") {
      return "green";
    }

    return "blue";
  }


  return (
    <MapContainer
      center={[18.5204, 73.8567]}
      zoom={12}
      style={{
        height: "100%",
        width: "100%",
        minHeight: "600px",
      }}
    >

      <TileLayer
        attribution="© OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />


      {/* Automatically zoom to route */}

      <MapController
        sourcePosition={sourcePosition}
        destinationPosition={destinationPosition}
        routes={routes}
      />


      {/* SOURCE MARKER */}

      {sourcePosition && (
        <Marker
          position={sourcePosition}
        >
          <Popup>
            <strong>
              Source
            </strong>

            <br />

            {source}
          </Popup>
        </Marker>
      )}


      {/* DESTINATION MARKER */}

      {destinationPosition && (
        <Marker
          position={destinationPosition}
        >
          <Popup>
            <strong>
              Destination
            </strong>

            <br />

            {destination}
          </Popup>
        </Marker>
      )}


      {/* ROUTES */}

      {routes.map(
        (route, index) => (
          <Polyline
            key={index}
            positions={route.geometry}
            pathOptions={{
              color: getRouteColor(route),

              weight:
                route.route_type === "Safest"
                  ? 7
                  : 5,

              opacity:
                route.route_type === "Safest"
                  ? 1
                  : 0.75,
            }}
          />
        )
      )}

    </MapContainer>
  );
}


export default MapView;