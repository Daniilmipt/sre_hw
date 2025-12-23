import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Кастомные метрики
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

// Конфигурация load profile теста
export const options = {
  stages: [
    // Ramp-up: постепенное увеличение нагрузки
    { duration: '2m', target: 20 },   // За 2 минуты до 20 пользователей
    { duration: '3m', target: 50 },   // За 3 минуты до 50 пользователей
    { duration: '5m', target: 100 },  // За 5 минут до 100 пользователей
    
    // Sustained load: поддержание стабильной нагрузки
    { duration: '10m', target: 100 }, // 10 минут на 100 пользователях
    
    // Spike: кратковременный пик нагрузки
    { duration: '2m', target: 200 },  // Резкий скачок до 200 пользователей
    { duration: '3m', target: 200 },  // Удержание пика 3 минуты
    
    // Ramp-down: постепенное снижение нагрузки
    { duration: '5m', target: 50 },   // Снижение до 50 пользователей
    { duration: '2m', target: 0 },    // Полное завершение
  ],
  
  thresholds: {
    // Пороги для load теста (более мягкие чем smoke)
    http_req_duration: ['p(95)<2000', 'p(99)<5000'],  // 95% < 2s, 99% < 5s
    http_req_failed: ['rate<0.1'],                     // < 10% ошибок
    http_reqs: ['rate>50'],                            // Минимум 50 запросов/сек
    errors: ['rate<0.1'],                              // < 10% ошибок
  },
};

const BASE_URL = 'http://77.105.182.79';
const HEADERS = {
  'Host': 'student2-api.autobase.tech',
};

// Список городов для тестирования (можно расширить)
const CITY_IDS = [1, 2, 3, 4, 5];

// Функция для получения случайного города
function getRandomCity() {
  return CITY_IDS[Math.floor(Math.random() * CITY_IDS.length)];
}

// Сценарий 1: Получение информации о городе
function getCity(cityId) {
  const res = http.get(`${BASE_URL}/Cities/${cityId}`, { headers: HEADERS });
  
  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'response has data': (r) => r.body.length > 0,
    'response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  errorRate.add(!success);
  responseTime.add(res.timings.duration);
  
  return res;
}

// Сценарий 2: Получение списка городов (если такой endpoint существует)
function getCities() {
  const res = http.get(`${BASE_URL}/Cities`, { headers: HEADERS });
  
  const success = check(res, {
    'status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  errorRate.add(!success);
  responseTime.add(res.timings.duration);
  
  return res;
}

// Основная функция виртуального пользователя
export default function () {
  // Имитация поведения пользователя: 70% запросов к конкретному городу, 30% к списку
  const scenario = Math.random();
  
  if (scenario < 0.7) {
    // Запрос конкретного города
    const cityId = getRandomCity();
    getCity(cityId);
  } else {
    // Запрос списка городов
    getCities();
  }
  
  // Реалистичная задержка между запросами (0-0.5 секунды)
  sleep(Math.random() * 0.5);
}

