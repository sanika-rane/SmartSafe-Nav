const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

async function parseJsonResponse(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

export async function getLocations() {
  const response = await fetch(`${BASE_URL}/locations`);

  if (!response.ok) {
    throw new Error("Unable to fetch locations");
  }

  return response.json();
}

export async function getCoordinates(location) {
  const response = await fetch(
    `${BASE_URL}/coordinates?location=${encodeURIComponent(location)}`
  );

  if (!response.ok) {
    throw new Error("Unable to fetch coordinates");
  }

  return response.json();
}
export async function predictRoute(
  source,
  destination,
  time
) {
  const response = await fetch(
    `${BASE_URL}/predict-route`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        source: source,
        destination: destination,
        time: time,
      }),
    }
  );

  const data = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(
      data.error || "Unable to predict route"
    );
  }

  return data;
}
export async function getSafeRoutes(
  source,
  destination,
  time
) {
  const response = await fetch(
    `${BASE_URL}/safe-routes`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        source,
        destination,
        time,
      }),
    }
  );

  const data = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(
      data.error || "Unable to find safe routes"
    );
  }

  return data;
}
