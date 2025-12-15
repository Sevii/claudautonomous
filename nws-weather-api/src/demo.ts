import * as fs from 'fs';
import * as path from 'path';

// Mock data based on real NWS API response structure
const mockForecastData = {
  properties: {
    updated: new Date().toISOString(),
    units: 'us',
    forecastGenerator: 'Demo Generator',
    generatedAt: new Date().toISOString(),
    updateTime: new Date().toISOString(),
    validTimes: '2024-01-01T00:00:00+00:00/P7D',
    elevation: {
      value: 282.8544,
      unitCode: 'wmoUnit:m'
    },
    periods: [
      {
        number: 1,
        name: 'This Afternoon',
        startTime: '2024-01-15T14:00:00-06:00',
        endTime: '2024-01-15T18:00:00-06:00',
        isDaytime: true,
        temperature: 45,
        temperatureUnit: 'F',
        temperatureTrend: null,
        windSpeed: '10 mph',
        windDirection: 'S',
        icon: 'https://api.weather.gov/icons/land/day/few?size=medium',
        shortForecast: 'Sunny',
        detailedForecast: 'Sunny, with a high near 45. South wind around 10 mph.'
      },
      {
        number: 2,
        name: 'Tonight',
        startTime: '2024-01-15T18:00:00-06:00',
        endTime: '2024-01-16T06:00:00-06:00',
        isDaytime: false,
        temperature: 32,
        temperatureUnit: 'F',
        temperatureTrend: null,
        windSpeed: '5 to 10 mph',
        windDirection: 'S',
        icon: 'https://api.weather.gov/icons/land/night/few?size=medium',
        shortForecast: 'Mostly Clear',
        detailedForecast: 'Mostly clear, with a low around 32. South wind 5 to 10 mph.'
      },
      {
        number: 3,
        name: 'Tuesday',
        startTime: '2024-01-16T06:00:00-06:00',
        endTime: '2024-01-16T18:00:00-06:00',
        isDaytime: true,
        temperature: 52,
        temperatureUnit: 'F',
        temperatureTrend: 'rising',
        windSpeed: '10 to 15 mph',
        windDirection: 'S',
        icon: 'https://api.weather.gov/icons/land/day/sct?size=medium',
        shortForecast: 'Partly Sunny',
        detailedForecast: 'Partly sunny, with a high near 52. South wind 10 to 15 mph, with gusts as high as 25 mph.'
      },
      {
        number: 4,
        name: 'Tuesday Night',
        startTime: '2024-01-16T18:00:00-06:00',
        endTime: '2024-01-17T06:00:00-06:00',
        isDaytime: false,
        temperature: 38,
        temperatureUnit: 'F',
        temperatureTrend: null,
        windSpeed: '10 mph',
        windDirection: 'S',
        icon: 'https://api.weather.gov/icons/land/night/bkn?size=medium',
        shortForecast: 'Mostly Cloudy',
        detailedForecast: 'Mostly cloudy, with a low around 38. South wind around 10 mph.'
      },
      {
        number: 5,
        name: 'Wednesday',
        startTime: '2024-01-17T06:00:00-06:00',
        endTime: '2024-01-17T18:00:00-06:00',
        isDaytime: true,
        temperature: 48,
        temperatureUnit: 'F',
        temperatureTrend: null,
        windSpeed: '10 to 15 mph',
        windDirection: 'NW',
        icon: 'https://api.weather.gov/icons/land/day/rain_showers,40?size=medium',
        shortForecast: 'Chance Rain Showers',
        detailedForecast: 'A chance of rain showers. Mostly cloudy, with a high near 48. Northwest wind 10 to 15 mph. Chance of precipitation is 40%.'
      },
      {
        number: 6,
        name: 'Wednesday Night',
        startTime: '2024-01-17T18:00:00-06:00',
        endTime: '2024-01-18T06:00:00-06:00',
        isDaytime: false,
        temperature: 28,
        temperatureUnit: 'F',
        temperatureTrend: null,
        windSpeed: '10 to 15 mph',
        windDirection: 'N',
        icon: 'https://api.weather.gov/icons/land/night/rain_showers,30/bkn?size=medium',
        shortForecast: 'Slight Chance Rain Showers then Mostly Cloudy',
        detailedForecast: 'A slight chance of rain showers before midnight. Mostly cloudy, with a low around 28. North wind 10 to 15 mph. Chance of precipitation is 30%.'
      },
      {
        number: 7,
        name: 'Thursday',
        startTime: '2024-01-18T06:00:00-06:00',
        endTime: '2024-01-18T18:00:00-06:00',
        isDaytime: true,
        temperature: 42,
        temperatureUnit: 'F',
        temperatureTrend: null,
        windSpeed: '10 mph',
        windDirection: 'N',
        icon: 'https://api.weather.gov/icons/land/day/bkn?size=medium',
        shortForecast: 'Partly Sunny',
        detailedForecast: 'Partly sunny, with a high near 42. North wind around 10 mph.'
      },
      {
        number: 8,
        name: 'Thursday Night',
        startTime: '2024-01-18T18:00:00-06:00',
        endTime: '2024-01-19T06:00:00-06:00',
        isDaytime: false,
        temperature: 25,
        temperatureUnit: 'F',
        temperatureTrend: null,
        windSpeed: '5 mph',
        windDirection: 'N',
        icon: 'https://api.weather.gov/icons/land/night/few?size=medium',
        shortForecast: 'Mostly Clear',
        detailedForecast: 'Mostly clear, with a low around 25. North wind around 5 mph becoming calm in the evening.'
      }
    ]
  }
};

// HTML Generator (same as main app)
class HTMLGenerator {
  generateHTML(forecast: any, location: string): string {
    const periods = forecast.properties.periods;
    const updated = new Date(forecast.properties.updated).toLocaleString();

    const periodsHTML = periods.map((period: any) => `
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

    .demo-notice {
      background: rgba(255, 193, 7, 0.2);
      border: 2px solid rgba(255, 193, 7, 0.5);
      border-radius: 8px;
      padding: 15px;
      margin: 20px 0;
      text-align: center;
      color: white;
      font-weight: 500;
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
      <div class="demo-notice">
        📋 DEMO MODE - Using sample data. Run the main app to fetch live weather data.
      </div>
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

// Main demo function
function main() {
  console.log('🌤️  NWS Weather API Demo (Mock Data)\n');

  const locationName = 'Kansas City, MO (Demo)';

  console.log(`📍 Generating demo forecast for ${locationName}...`);
  console.log('   Using mock data...');

  const generator = new HTMLGenerator();
  const html = generator.generateHTML(mockForecastData, locationName);

  const outputPath = path.join(__dirname, '..', 'forecast-demo.html');
  fs.writeFileSync(outputPath, html);

  console.log(`\n✅ Success! Demo forecast saved to: ${outputPath}`);
  console.log(`\n💡 Open forecast-demo.html in your browser to see the HTML/CSS rendering.`);
  console.log(`\n📊 Demo includes ${mockForecastData.properties.periods.length} forecast periods`);
  console.log(`\n🔄 To fetch real data, run: npm start`);
}

main();
