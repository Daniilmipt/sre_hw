import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 50 },
    { duration: '1m', target: 100 },
    { duration: '1m', target: 200 },
    { duration: '1m', target: 300 },
    { duration: '1m', target: 400 },
    { duration: '1m', target: 500 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = 'http://localhost:8080';
const ENDPOINTS = {
  WEATHER_FORECAST: '/WeatherForecast',
  CITIES: '/Cities',
  CITY_BY_ID: (id) => `/Cities/${id}`,
};

/**
 * Safely parse JSON response
 */
function parseJsonResponse(response) {
  try {
    return response.json();
  } catch (error) {
    return null;
  }
}

/**
 * Extract first city ID from cities array
 */
function extractFirstCityId(cities) {
  if (!Array.isArray(cities) || cities.length === 0) {
    return null;
  }
  return cities[0]?.id ?? null;
}

/**
 * Test weather forecast endpoint
 */
function testWeatherForecast() {
  const url = `${BASE_URL}${ENDPOINTS.WEATHER_FORECAST}`;
  const response = http.get(url);
  
  check(response, {
    'forecast 200': (r) => r.status === 200,
  });
}

/**
 * Test cities endpoint and return first city ID
 */
function testCities() {
  const url = `${BASE_URL}${ENDPOINTS.CITIES}`;
  const response = http.get(url);
  
  const cities = parseJsonResponse(response);
  const cityId = extractFirstCityId(cities);
  
  check(response, {
    'cities 200': (r) => r.status === 200,
    'cities non-empty': () => cityId !== null,
  });
  
  return cityId;
}

/**
 * Test city by ID endpoint
 */
function testCityById(cityId) {
  if (cityId === null) {
    return;
  }
  
  const url = `${BASE_URL}${ENDPOINTS.CITY_BY_ID(cityId)}`;
  const response = http.get(url);
  
  const cityData = parseJsonResponse(response);
  
  check(response, {
    'city 200': (r) => r.status === 200,
    'city has id': () => cityData?.id !== undefined,
  });
}

export default function () {
  testWeatherForecast();
  
  const cityId = testCities();
  
  testCityById(cityId);
  
  sleep(0.05);
}
