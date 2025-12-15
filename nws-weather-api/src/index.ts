import fetch from 'node-fetch';
import * as fs from 'fs';
import * as path from 'path';

// NWS API Types
interface Point {
  properties: {
    forecast: string;
    forecastHourly: string;
    forecastGridData: string;
    observationStations: string;
  };
}

interface Period {
  number: number;
  name: string;
  startTime: string;
  endTime: string;
  isDaytime: boolean;
  temperature: number;
  temperatureUnit: string;
  temperatureTrend: string | null;
  windSpeed: string;
  windDirection: string;
  icon: string;
  shortForecast: string;
  detailedForecast: string;
}

interface Forecast {
  properties: {
    updated: string;
    units: string;
    forecastGenerator: string;
    generatedAt: string;
    updateTime: string;
    validTimes: string;
    elevation: {
      value: number;
      unitCode: string;
    };
    periods: Period[];
  };
}

// NWS API Client
class NWSClient {
  private readonly baseUrl = 'https://api.weather.gov';
  private readonly userAgent = '(NWS-Example-App, contact@example.com)';

  async getPoint(latitude: number, longitude: number): Promise<Point> {
    const url = `${this.baseUrl}/points/${latitude},${longitude}`;
    const response = await fetch(url, {
      headers: {
        'User-Agent': this.userAgent,
        'Accept': 'application/geo+json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch point data: ${response.status} ${response.statusText}`);
    }

    return await response.json() as Point;
  }

  async getForecast(forecastUrl: string): Promise<Forecast> {
    const response = await fetch(forecastUrl, {
      headers: {
        'User-Agent': this.userAgent,
        'Accept': 'application/geo+json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch forecast: ${response.status} ${response.statusText}`);
    }

    return await response.json() as Forecast;
  }
}

// HTML Generator
class HTMLGenerator {
  generateHTML(forecast: Forecast, location: string): string {
    const periods = forecast.properties.periods;
    const updated = new Date(forecast.properties.updated).toLocaleString();

    const periodsHTML = periods.map(period => `
      <div class="forecast-card ${period.isDaytime ? 'day' : 'night'}">
        <div class="forecast-header">
          <h3>${period.name}</h3>
          <div class="temperature">${period.temperature}°${period.temperatureUnit}</div>
        </div>
        <div class="forecast-icon">
          <img src="${period.icon}" alt="${period.shortForecast}" />
        </div>
        <div class="forecast-details">
          <div class="short-forecast">${period.shortForecast}</div>
          <div class="wind">
            <span class="label">Wind:</span> ${period.windSpeed} ${period.windDirection}
          </div>
          <div class="detailed-forecast">${period.detailedForecast}</div>
        </div>
      </div>
    `).join('');

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NWS Weather Forecast - ${location}</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
    }

    header {
      text-align: center;
      color: white;
      margin-bottom: 30px;
    }

    h1 {
      font-size: 2.5em;
      margin-bottom: 10px;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }

    .location {
      font-size: 1.2em;
      opacity: 0.9;
    }

    .updated {
      font-size: 0.9em;
      opacity: 0.8;
      margin-top: 5px;
    }

    .forecast-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }

    .forecast-card {
      background: white;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .forecast-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 12px rgba(0,0,0,0.15);
    }

    .forecast-card.day {
      border-top: 4px solid #FDB813;
    }

    .forecast-card.night {
      border-top: 4px solid #2C3E50;
    }

    .forecast-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding-bottom: 15px;
      border-bottom: 2px solid #f0f0f0;
    }

    .forecast-header h3 {
      color: #333;
      font-size: 1.3em;
    }

    .temperature {
      font-size: 2em;
      font-weight: bold;
      color: #667eea;
    }

    .forecast-icon {
      text-align: center;
      margin: 15px 0;
    }

    .forecast-icon img {
      width: 100px;
      height: 100px;
    }

    .forecast-details {
      color: #555;
    }

    .short-forecast {
      font-size: 1.1em;
      font-weight: 600;
      color: #333;
      margin-bottom: 10px;
      text-align: center;
    }

    .wind {
      margin: 10px 0;
      padding: 8px;
      background: #f8f9fa;
      border-radius: 6px;
      font-size: 0.95em;
    }

    .wind .label {
      font-weight: 600;
      color: #667eea;
    }

    .detailed-forecast {
      margin-top: 12px;
      line-height: 1.6;
      font-size: 0.95em;
      color: #666;
    }

    footer {
      text-align: center;
      color: white;
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid rgba(255,255,255,0.2);
      font-size: 0.9em;
    }

    footer a {
      color: white;
      text-decoration: underline;
    }

    @media (max-width: 768px) {
      h1 {
        font-size: 2em;
      }

      .forecast-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🌤️ Weather Forecast</h1>
      <div class="location">${location}</div>
      <div class="updated">Last Updated: ${updated}</div>
    </header>

    <div class="forecast-grid">
      ${periodsHTML}
    </div>

    <footer>
      <p>Data provided by the National Weather Service</p>
      <p><a href="https://www.weather.gov" target="_blank">weather.gov</a></p>
    </footer>
  </div>
</body>
</html>`;
  }
}

// Main application
async function main() {
  try {
    console.log('🌤️  NWS Weather API Example\n');

    // Example coordinates (Kansas City, MO)
    // You can change these to any US location
    const latitude = 39.0997;
    const longitude = -94.5786;
    const locationName = 'Kansas City, MO';

    console.log(`📍 Fetching forecast for ${locationName} (${latitude}, ${longitude})...`);

    const client = new NWSClient();

    // Step 1: Get the point data to find the forecast URL
    console.log('   Retrieving grid point data...');
    const point = await client.getPoint(latitude, longitude);

    // Step 2: Get the actual forecast
    console.log('   Fetching forecast data...');
    const forecast = await client.getForecast(point.properties.forecast);

    // Step 3: Generate HTML
    console.log('   Generating HTML...');
    const generator = new HTMLGenerator();
    const html = generator.generateHTML(forecast, locationName);

    // Step 4: Write to file
    const outputPath = path.join(__dirname, '..', 'forecast.html');
    fs.writeFileSync(outputPath, html);

    console.log(`\n✅ Success! Forecast saved to: ${outputPath}`);
    console.log(`\n💡 Open forecast.html in your browser to view the weather forecast.`);
    console.log(`\n📊 Forecast includes ${forecast.properties.periods.length} periods`);

  } catch (error) {
    console.error('❌ Error:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// Run the application
main();
