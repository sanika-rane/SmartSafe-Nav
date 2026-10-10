import { useEffect, useState } from "react";
import { getLocations } from "../services/api";

function RouteForm({
  source,
  destination,
  time,
  setSource,
  setDestination,
  setTime,
  onFindRoute,
  loading,
}) {

  const [locations, setLocations] = useState([]);

  useEffect(() => {

    async function fetchLocations() {

      try {

        const data = await getLocations();

        setLocations(data.locations);

        if (data.locations.length > 1) {

          if (source === "") {
            setSource(data.locations[0]);
          }

          if (destination === "") {
            setDestination(data.locations[1]);
          }

        }

      } catch (error) {

        console.log("Location error:", error);

      }

    }

    fetchLocations();

  }, [
    source,
    destination,
    setSource,
    setDestination,
  ]);

  return (

    <div className="route-form">

      {/* SOURCE */}

      <div className="form-group">

        <label>📍 Select Source</label>

        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
        >

          {locations.map((location) => (

            <option
              key={location}
              value={location}
            >
              {location}
            </option>

          ))}

        </select>

      </div>


      {/* DESTINATION */}

      <div className="form-group">

        <label>📍 Select Destination</label>

        <select
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
        >

          {locations.map((location) => (

            <option
              key={location}
              value={location}
            >
              {location}
            </option>

          ))}

        </select>

      </div>


      {/* TIME */}

      <div className="form-group">

        <label>🕐 Travel Time</label>

        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
        />

      </div>


      {/* BUTTON */}

      <button
  className="find-route-button"
  onClick={onFindRoute}
  disabled={loading}
>
  {loading
    ? "Finding Safest Route..."
    : "🔍 Find Safest Route"}
</button>

    </div>

  );
}

export default RouteForm;
