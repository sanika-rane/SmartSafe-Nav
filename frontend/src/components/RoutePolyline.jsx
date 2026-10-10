import { useEffect, useState } from "react";
import { Polyline } from "react-leaflet";

function RoutePolyline({ source, destination }) {

  const [route, setRoute] = useState([]);

  useEffect(() => {

    async function fetchRoute() {

      try {

        const url =
          `https://router.project-osrm.org/route/v1/driving/` +
          `${source[1]},${source[0]};${destination[1]},${destination[0]}` +
          `?overview=full&geometries=geojson`;

        const response = await fetch(url);

        const data = await response.json();

        if (data.routes && data.routes.length > 0) {

          const coordinates =
            data.routes[0].geometry.coordinates.map(
              (coord) => [coord[1], coord[0]]
            );

          setRoute(coordinates);

        }

      } catch (error) {

        console.log(error);

      }

    }

    fetchRoute();

  }, [source, destination]);

  if (route.length === 0) return null;

  return (

    <Polyline
      positions={route}
      pathOptions={{
        color: "blue",
        weight: 6,
      }}
    />

  );

}

export default RoutePolyline;