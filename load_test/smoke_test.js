import http from 'k6/http';
import { check, sleep } from 'k6';

// Конфигурация smoke теста (малая нагрузка)
export const options = {
  vus: 5,              // 5 виртуальных пользователей
  duration: '1m',      // 1 минута
  
  thresholds: {
    http_req_duration: ['p(95)<1000'],  // 95% запросов < 1s
    http_req_failed: ['rate<0.05'],     // < 5% ошибок
  },
};

const BASE_URL = 'http://77.105.182.79';
const HEADERS = {
  'Host': 'student5-api.autobase.tech',
};

export default function () {
  // Простой запрос к API
  const res = http.get(`${BASE_URL}/Cities/1`, { headers: HEADERS });
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 1s': (r) => r.timings.duration < 1000,
  });
  
  sleep(1); // 1 секунда между запросами
}

