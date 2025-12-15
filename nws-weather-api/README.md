# National Weather Service API Example

A TypeScript example demonstrating how to fetch and render weather forecast data from the National Weather Service API.

## Features

- ✅ Fetches real-time weather data from the NWS API
- ✅ Generates a beautiful HTML/CSS visualization
- ✅ Displays multi-day forecast with detailed information
- ✅ Responsive design that works on all devices
- ✅ TypeScript for type safety
- ✅ Simple single-script execution

## How It Works

The National Weather Service provides a free public API for accessing weather data. This example demonstrates the two-step process:

1. **Point Lookup**: First, we query the `/points/{latitude},{longitude}` endpoint to get the forecast grid and office information for a location
2. **Forecast Retrieval**: Using the forecast URL from step 1, we fetch the actual weather forecast data
3. **HTML Generation**: The forecast data is rendered into a styled HTML page

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn

## Setup

1. Install dependencies:

```bash
npm install
```

## Usage

Run the example:

```bash
npm start
```

Or for development with ts-node:

```bash
npm run dev
```

This will:
1. Fetch the weather forecast for Kansas City, MO (default location)
2. Generate an HTML file called `forecast.html` in the project root
3. Open `forecast.html` in your browser to view the forecast

## Customizing the Location

To fetch weather for a different location, edit `src/index.ts` and change these values:

```typescript
const latitude = 39.0997;   // Your latitude
const longitude = -94.5786;  // Your longitude
const locationName = 'Kansas City, MO';  // Display name
```

You can find coordinates for any US location using [latlong.net](https://www.latlong.net/).

## API Details

### Required Headers

The NWS API requires a `User-Agent` header to identify your application:

```typescript
headers: {
  'User-Agent': '(YourApp, contact@example.com)',
  'Accept': 'application/geo+json'
}
```

### Key Endpoints

- **Points**: `https://api.weather.gov/points/{lat},{lon}`
  - Returns forecast URLs and grid information

- **Forecast**: `https://api.weather.gov/gridpoints/{office}/{gridX},{gridY}/forecast`
  - Returns the actual forecast periods

### Response Data

Each forecast period includes:
- Period name (e.g., "Tonight", "Tuesday")
- Temperature and unit
- Wind speed and direction
- Short and detailed forecasts
- Weather icon URL
- Day/night indicator

## Output

The generated HTML includes:
- Responsive grid layout
- Day/night visual indicators
- Temperature displays
- Weather icons from NWS
- Detailed forecasts
- Wind information
- Last updated timestamp

## Project Structure

```
nws-weather-api/
├── src/
│   └── index.ts          # Main application code
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
└── README.md            # This file
```

## API Documentation

For more information about the National Weather Service API:
- [Official API Documentation](https://www.weather.gov/documentation/services-web-api)
- [OpenAPI Specification](https://api.weather.gov/openapi.json)

## Notes

- The NWS API only provides data for US locations
- No API key is required - it's completely free
- Rate limits are generous for typical use cases
- All times are in ISO-8601 format
- The API returns GeoJSON formatted responses by default

## License

MIT
