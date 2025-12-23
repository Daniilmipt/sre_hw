#!/usr/bin/env python3
"""
Анализ результатов нагрузочного теста k6 из results_local.json
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from statistics import mean, median, stdev
from typing import Dict, List, Any

def percentile(data: List[float], p: float) -> float:
    """Вычисляет перцентиль"""
    if not data:
        return 0
    sorted_data = sorted(data)
    index = (len(sorted_data) - 1) * p / 100
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_data):
        return sorted_data[-1]
    weight = index - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight

def analyze_k6_results(file_path: str):
    """Анализирует результаты k6"""
    
    # Структуры для хранения данных
    http_reqs = []
    http_req_duration = []
    http_req_duration_by_endpoint = defaultdict(list)
    http_req_failed = []
    checks = defaultdict(int)
    iterations = []
    iteration_duration = []
    data_sent = []
    data_received = []
    
    # Временные метки
    timestamps = []
    
    # Читаем файл построчно (JSON Lines формат)
    print(f"Чтение файла {file_path}...")
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                
                if data.get('type') == 'Point':
                    metric = data.get('metric')
                    point_data = data.get('data', {})
                    value = point_data.get('value')
                    tags = point_data.get('tags', {})
                    time_str = point_data.get('time')
                    
                    if time_str:
                        try:
                            ts = datetime.fromisoformat(time_str.replace('+03:00', '+03:00'))
                            timestamps.append(ts)
                        except:
                            pass
                    
                    if metric == 'http_reqs':
                        http_reqs.append({
                            'value': value,
                            'url': tags.get('url', ''),
                            'status': tags.get('status', ''),
                            'time': time_str
                        })
                    
                    elif metric == 'http_req_duration':
                        duration = value
                        http_req_duration.append(duration)
                        url = tags.get('url', '')
                        # Извлекаем эндпоинт из URL
                        endpoint = url.split('/')[-1] if url else 'unknown'
                        if '/Cities/' in url:
                            endpoint = f"/Cities/{{id}}"
                        elif '/Cities' in url:
                            endpoint = "/Cities"
                        elif '/WeatherForecast' in url:
                            endpoint = "/WeatherForecast"
                        http_req_duration_by_endpoint[endpoint].append(duration)
                    
                    elif metric == 'http_req_failed':
                        http_req_failed.append(value)
                    
                    elif metric == 'checks':
                        check_name = tags.get('check', '')
                        checks[check_name] += value
                    
                    elif metric == 'iterations':
                        iterations.append(value)
                    
                    elif metric == 'iteration_duration':
                        iteration_duration.append(value)
                    
                    elif metric == 'data_sent':
                        data_sent.append(value)
                    
                    elif metric == 'data_received':
                        data_received.append(value)
            
            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга строки {line_num}: {e}", file=sys.stderr)
                continue
    
    # Вычисляем статистику
    print("\n" + "="*80)
    print("АНАЛИЗ РЕЗУЛЬТАТОВ НАГРУЗОЧНОГО ТЕСТА K6")
    print("="*80)
    
    # Временной диапазон
    if timestamps:
        start_time = min(timestamps)
        end_time = max(timestamps)
        duration = (end_time - start_time).total_seconds()
        print(f"\n📅 Временной диапазон:")
        print(f"   Начало: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Конец:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Длительность: {duration:.1f} секунд ({duration/60:.1f} минут)")
    
    # HTTP запросы
    print(f"\n📊 HTTP ЗАПРОСЫ:")
    total_requests = len(http_reqs)
    print(f"   Всего запросов: {total_requests}")
    
    # Статусы
    status_counts = defaultdict(int)
    for req in http_reqs:
        status_counts[req['status']] += 1
    
    print(f"\n   Статусы ответов:")
    for status, count in sorted(status_counts.items()):
        percentage = (count / total_requests * 100) if total_requests > 0 else 0
        print(f"     {status}: {count} ({percentage:.1f}%)")
    
    # Эндпоинты
    endpoint_counts = defaultdict(int)
    for req in http_reqs:
        url = req['url']
        if '/Cities/' in url and url.count('/') >= 4:
            endpoint_counts['/Cities/{id}'] += 1
        elif '/Cities' in url:
            endpoint_counts['/Cities'] += 1
        elif '/WeatherForecast' in url:
            endpoint_counts['/WeatherForecast'] += 1
    
    print(f"\n   Запросы по эндпоинтам:")
    for endpoint, count in sorted(endpoint_counts.items()):
        percentage = (count / total_requests * 100) if total_requests > 0 else 0
        print(f"     {endpoint}: {count} ({percentage:.1f}%)")
    
    # Длительность запросов
    if http_req_duration:
        print(f"\n⏱️  ДЛИТЕЛЬНОСТЬ HTTP ЗАПРОСОВ (мс):")
        print(f"   Всего измерений: {len(http_req_duration)}")
        print(f"   Минимум:  {min(http_req_duration):.2f} мс")
        print(f"   Максимум: {max(http_req_duration):.2f} мс")
        print(f"   Среднее:  {mean(http_req_duration):.2f} мс")
        print(f"   Медиана:  {median(http_req_duration):.2f} мс")
        if len(http_req_duration) > 1:
            print(f"   Стд. откл.: {stdev(http_req_duration):.2f} мс")
        print(f"   p50: {percentile(http_req_duration, 50):.2f} мс")
        print(f"   p90: {percentile(http_req_duration, 90):.2f} мс")
        print(f"   p95: {percentile(http_req_duration, 95):.2f} мс")
        print(f"   p99: {percentile(http_req_duration, 99):.2f} мс")
        
        # Проверка порога p95 < 500
        p95_value = percentile(http_req_duration, 95)
        threshold_95 = 500
        status = "✅ ПРОЙДЕН" if p95_value < threshold_95 else "❌ НЕ ПРОЙДЕН"
        print(f"\n   Порог p95 < {threshold_95} мс: {status} (фактическое значение: {p95_value:.2f} мс)")
        
        # Статистика по эндпоинтам
        print(f"\n   Длительность по эндпоинтам:")
        for endpoint, durations in sorted(http_req_duration_by_endpoint.items()):
            if durations:
                print(f"     {endpoint}:")
                print(f"       Запросов: {len(durations)}")
                print(f"       Среднее:  {mean(durations):.2f} мс")
                print(f"       Медиана:  {median(durations):.2f} мс")
                print(f"       p95:      {percentile(durations, 95):.2f} мс")
                print(f"       p99:      {percentile(durations, 99):.2f} мс")
    
    # Ошибки
    print(f"\n❌ ОШИБКИ:")
    total_failed = sum(1 for v in http_req_failed if v > 0)
    failed_rate = (total_failed / total_requests * 100) if total_requests > 0 else 0
    print(f"   Запросов с ошибками: {total_failed}")
    print(f"   Процент ошибок: {failed_rate:.2f}%")
    
    # Проверка порога rate < 0.01
    threshold_failed = 0.01
    actual_rate = total_failed / total_requests if total_requests > 0 else 0
    status = "✅ ПРОЙДЕН" if actual_rate < threshold_failed else "❌ НЕ ПРОЙДЕН"
    print(f"   Порог rate < {threshold_failed}: {status} (фактическое значение: {actual_rate:.4f})")
    
    # Checks
    print(f"\n✅ ПРОВЕРКИ (CHECKS):")
    total_checks = sum(checks.values())
    for check_name, count in sorted(checks.items()):
        print(f"   {check_name}: {count}")
    print(f"   Всего проверок: {total_checks}")
    
    # Итерации
    if iterations:
        total_iterations = sum(iterations)
        print(f"\n🔄 ИТЕРАЦИИ:")
        print(f"   Всего итераций: {total_iterations}")
    
    if iteration_duration:
        print(f"\n   Длительность итераций (мс):")
        print(f"     Минимум:  {min(iteration_duration):.2f} мс")
        print(f"     Максимум: {max(iteration_duration):.2f} мс")
        print(f"     Среднее:  {mean(iteration_duration):.2f} мс")
        print(f"     Медиана:  {median(iteration_duration):.2f} мс")
        print(f"     p95:      {percentile(iteration_duration, 95):.2f} мс")
    
    # Данные
    if data_sent:
        total_sent = sum(data_sent)
        print(f"\n📤 ДАННЫЕ:")
        print(f"   Отправлено: {total_sent:,} байт ({total_sent/1024:.2f} KB)")
    
    if data_received:
        total_received = sum(data_received)
        print(f"   Получено:   {total_received:,} байт ({total_received/1024:.2f} KB)")
    
    # RPS (Requests Per Second)
    if timestamps and duration > 0:
        rps = total_requests / duration
        print(f"\n🚀 ПРОИЗВОДИТЕЛЬНОСТЬ:")
        print(f"   Средний RPS: {rps:.2f} запросов/сек")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    file_path = 'results_local.json'
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    try:
        analyze_k6_results(file_path)
    except FileNotFoundError:
        print(f"Ошибка: файл {file_path} не найден", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при анализе: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

