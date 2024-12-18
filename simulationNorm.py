import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import weibull_min
import csv
import random
import heapq

def simulate_server_and_disks(sim_duration, shape, server):
    """
    Симуляция работы сервера и его дисков с учётом отказов сервера и дисков.

    Args:
        sim_duration (float): Длительность симуляции в часах.
        shape (float): Параметр формы распределения Вейбулла.
        server (dict): Конфигурация сервера из config.json.

    Returns:
        tuple: Метрики сервера и список метрик дисков.
    """
    server_id = server['id']
    server_repair_cost = float(server['server_repair_cost_PLN'])  # Убедимся, что это float
    disks = server['disks']
    num_disks = len(disks)

    # Инициализация состояния сервера и дисков
    server_status = 'up'  # 'up' или 'down'
    disks_status = ['up'] * num_disks  # Список статусов дисков

    # Метрики сервера
    server_total_downtime = 0.0
    server_failures = 0
    server_total_repair_cost = 0.0
    server_total_lost_revenue = 0.0
    server_downtime_intervals = []
    server_downtime_start = None  # Для расчёта потерь дохода

    # Метрики дисков
    disks_results = []
    for disk in disks:
        disks_results.append({
            'downtime': 0.0,
            'failures': 0,
            'repair_cost_total': 0.0,
            'lost_revenue_total': 0.0,
            'mttr': 0.0,
            'mttf': 0.0,
            'availability_percent': 100.0,  # Инициализация доступности
            'downtime_intervals': []
        })

    # Суммарная потеря дохода всех дисков
    total_lost_revenue_per_hour = sum(float(disk['lost_revenue_per_hour_PLN']) for disk in disks)

    # События: (timestamp, event_type, component_index)
    # event_type: 'server_fail', 'server_repair', 'disk_fail', 'disk_repair'
    events = []
    heapq.heapify(events)

    # Генерация первого отказа сервера
    server_scale = sim_duration / 1.0  # Настройка масштаба для сервера (MTTF ≈ sim_duration)
    first_server_fail = weibull_min.rvs(shape, scale=server_scale)
    heapq.heappush(events, (first_server_fail, 'server_fail', None))

    # Генерация первого отказа каждого диска
    disk_scales = [sim_duration / 2.0 for _ in disks]  # Масштаб для дисков (MTTF ≈ sim_duration / 2)
    for i in range(num_disks):
        first_disk_fail = weibull_min.rvs(shape, scale=disk_scales[i])
        heapq.heappush(events, (first_disk_fail, 'disk_fail', i))

    current_time = 0.0

    while events:
        event = heapq.heappop(events)
        event_time, event_type, component_index = event

        if event_time > sim_duration:
            break

        # Обновление текущего времени
        current_time = event_time

        if event_type == 'server_fail':
            if server_status == 'up':
                server_status = 'down'
                server_failures += 1
                server_total_repair_cost += server_repair_cost
                server_downtime_start = current_time

                # Все диски считаются в простое из-за сервера
                for i in range(num_disks):
                    if disks_status[i] == 'up':
                        disks_status[i] = 'down'
                        # Добавить простои дисков из-за сервера
                        disks_results[i]['downtime_intervals'].append((current_time, None))  # Завершение позже

                # Генерация события ремонта сервера
                repair_time = random.uniform(1.5, 2.5)
                repair_finish = current_time + repair_time
                if repair_finish > sim_duration:
                    repair_finish = sim_duration
                heapq.heappush(events, (repair_finish, 'server_repair', None))

                # Добавить интервал простоя сервера
                server_downtime_intervals.append((current_time, repair_finish))
                server_total_downtime += (repair_finish - current_time)

        elif event_type == 'server_repair':
            if server_status == 'down':
                server_status = 'up'
                # Все диски восстанавливаются
                for i in range(num_disks):
                    if disks_status[i] == 'down':
                        disks_status[i] = 'up'
                        # Завершить интервал простоя диска, связанный с сервером
                        if disks_results[i]['downtime_intervals'] and disks_results[i]['downtime_intervals'][-1][1] is None:
                            start, _ = disks_results[i]['downtime_intervals'][-1]
                            downtime = current_time - start
                            disks_results[i]['downtime'] += downtime
                            # Не добавляем к lost_revenue_total, чтобы избежать двойного учёта
                            disks_results[i]['downtime_intervals'][-1] = (start, current_time)

                # Потери дохода сервера как сумма потерянных доходов всех дисков
                if server_downtime_start is not None:
                    server_lost_revenue = (current_time - server_downtime_start) * total_lost_revenue_per_hour
                    server_total_lost_revenue += server_lost_revenue

                # Генерация следующего отказа сервера
                next_server_fail = current_time + weibull_min.rvs(shape, scale=server_scale)
                if next_server_fail <= sim_duration:
                    heapq.heappush(events, (next_server_fail, 'server_fail', None))

        elif event_type == 'disk_fail':
            if server_status == 'up' and disks_status[component_index] == 'up':
                # Отказ диска
                disks_status[component_index] = 'down'
                disks_results[component_index]['failures'] += 1
                disks_results[component_index]['repair_cost_total'] += float(disks[component_index]['repair_cost_PLN'])
                disks_results[component_index]['downtime_intervals'].append((current_time, None))  # Завершение позже

                # Генерация события ремонта диска
                repair_time = random.uniform(1.5, 2.5)
                repair_finish = current_time + repair_time
                if repair_finish > sim_duration:
                    repair_finish = sim_duration
                heapq.heappush(events, (repair_finish, 'disk_repair', component_index))

        elif event_type == 'disk_repair':
            if server_status == 'up' and disks_status[component_index] == 'down':
                # Ремонт диска
                disks_status[component_index] = 'up'
                # Завершить интервал простоя диска
                if disks_results[component_index]['downtime_intervals'] and \
                   disks_results[component_index]['downtime_intervals'][-1][1] is None:
                    start, _ = disks_results[component_index]['downtime_intervals'][-1]
                    downtime = current_time - start
                    disks_results[component_index]['downtime'] += downtime

                    # Рассчитать потерю дохода
                    lost_revenue = downtime * float(disks[component_index]['lost_revenue_per_hour_PLN'])
                    disks_results[component_index]['lost_revenue_total'] += lost_revenue

                    disks_results[component_index]['downtime_intervals'][-1] = (start, current_time)

                # Генерация следующего отказа диска
                next_disk_fail = current_time + weibull_min.rvs(shape, scale=disk_scales[component_index])
                if next_disk_fail <= sim_duration:
                    heapq.heappush(events, (next_disk_fail, 'disk_fail', component_index))

    # Обработка открытых интервалов простоя после завершения симуляции
    # Для сервера
    if server_status == 'down' and server_downtime_start is not None:
        downtime = sim_duration - server_downtime_start
        server_total_downtime += downtime
        server_lost_revenue = downtime * total_lost_revenue_per_hour
        server_total_lost_revenue += server_lost_revenue
        server_downtime_intervals.append((server_downtime_start, sim_duration))

        # Закрываем простои дисков, вызванные простоями сервера
        for i in range(num_disks):
            if disks_status[i] == 'down' and disks_results[i]['downtime_intervals'] and \
               disks_results[i]['downtime_intervals'][-1][1] is None:
                start, _ = disks_results[i]['downtime_intervals'][-1]
                disk_downtime = sim_duration - start
                disks_results[i]['downtime'] += disk_downtime
                # Потеря дохода
                lost_revenue = disk_downtime * float(disks[i]['lost_revenue_per_hour_PLN'])
                disks_results[i]['lost_revenue_total'] += lost_revenue
                disks_results[i]['downtime_intervals'][-1] = (start, sim_duration)

    # Для дисков
    for i in range(num_disks):
        if disks_status[i] == 'down' and disks_results[i]['downtime_intervals'] and \
           disks_results[i]['downtime_intervals'][-1][1] is None:
            start, _ = disks_results[i]['downtime_intervals'][-1]
            disk_downtime = sim_duration - start
            disks_results[i]['downtime'] += disk_downtime
            # Потеря дохода
            lost_revenue = disk_downtime * float(disks[i]['lost_revenue_per_hour_PLN'])
            disks_results[i]['lost_revenue_total'] += lost_revenue
            disks_results[i]['downtime_intervals'][-1] = (start, sim_duration)

    # После симуляции, расчёт MTTR, MTTF и availability_percent для дисков
    for disk in disks_results:
        if disk['failures'] > 0:
            disk['mttr'] = disk['downtime'] / disk['failures']
            disk['mttf'] = sim_duration / disk['failures']
        else:
            disk['mttr'] = 0.0
            disk['mttf'] = sim_duration
        # Расчёт доступности
        disk['availability_percent'] = (1.0 - (disk['downtime'] / sim_duration)) * 100.0

    # Метрики сервера
    if server_failures > 0:
        server_mttr = server_total_downtime / server_failures
        server_mttf = sim_duration / server_failures
    else:
        server_mttr = 0.0
        server_mttf = sim_duration

    # Рассчитываем доступность для сервера
    server_availability_percent = (1.0 - (server_total_downtime / sim_duration)) * 100.0

    server_result = {
        'downtime': server_total_downtime,
        'failures': server_failures,
        'repair_cost_total': server_total_repair_cost,
        'lost_revenue': server_total_lost_revenue,
        'mttr': server_mttr,
        'mttf': server_mttf,
        'availability_percent': server_availability_percent
    }

    return server_result, disks_results

def main():
    # Установка фиксированного случайного начального seed для воспроизводимости
    random.seed(105)
    np.random.seed(105)

    # Загрузка конфигурации
    with open('config.json', 'r') as f:
        config = json.load(f)

    sim_duration = float(config['time_period_hours'])
    shape = float(config['weibull_shape'])
    currency = config['currency']
    servers = config['servers']

    all_server_results = []
    all_disk_results = []
    disk_labels = []
    server_labels = []

    for server in servers:
        server_label = f"Server{server['id']}"
        server_result, disks_results = simulate_server_and_disks(sim_duration, shape, server)
        all_server_results.append((server_label, server_result))
        server_labels.append(server_label)

        for i, disk in enumerate(disks_results):
            disk_label = f"S{server['id']}D{i + 1}"
            all_disk_results.append((disk_label, disk))
            disk_labels.append(disk_label)

    # Вывод результатов по дискам
    print("Wyniki dla dysków:")
    for label, disk in all_disk_results:
        print(f"{label}: Przestój={disk['downtime']:.2f}h, Koszt naprawy={disk['repair_cost_total']:.2f}{currency}, "
              f"Utracone przychody={disk['lost_revenue_total']:.2f}{currency}, "
              f"MTTR={disk['mttr']:.2f}h, MTTF={disk['mttf']:.2f}h, Dostępność={disk['availability_percent']:.2f}%")

    # Вывод результатов по серверам
    print("\nWyniki dla serwerów:")
    for label, server in all_server_results:
        print(
            f"{label}: Przestój={server['downtime']:.2f}h, Koszt naprawy={server['repair_cost_total']:.2f}{currency}, "
            f"Utracone przychody={server['lost_revenue']:.2f}{currency}, "
            f"MTTR={server['mttr']:.2f}h, MTTF={server['mttf']:.2f}h, Dostępność={server['availability_percent']:.2f}%")

    # Сохранение результатов дисков в CSV
    csv_filename_disks = 'results_disks.csv'
    with open(csv_filename_disks, 'w', newline='') as csvfile:
        fieldnames = ['server_disk', 'downtime_hours', 'repair_cost', 'lost_revenue', 'mttr', 'mttf', 'availability_percent']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for label, disk in all_disk_results:
            writer.writerow({
                'server_disk': label,
                'downtime_hours': f"{disk['downtime']:.2f}",
                'repair_cost': f"{disk['repair_cost_total']:.2f}",
                'lost_revenue': f"{disk['lost_revenue_total']:.2f}",
                'mttr': f"{disk['mttr']:.2f}",
                'mttf': f"{disk['mttf']:.2f}",
                'availability_percent': f"{disk['availability_percent']:.2f}",
            })

    # Сохранение результатов серверов в CSV
    csv_filename_servers = 'results_servers.csv'
    with open(csv_filename_servers, 'w', newline='') as csvfile:
        fieldnames = ['server', 'downtime_hours', 'repair_cost', 'lost_revenue', 'mttr', 'mttf', 'availability_percent']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for label, server in all_server_results:
            writer.writerow({
                'server': label,
                'downtime_hours': f"{server['downtime']:.2f}",
                'repair_cost': f"{server['repair_cost_total']:.2f}",
                'lost_revenue': f"{server['lost_revenue']:.2f}",
                'mttr': f"{server['mttr']:.2f}",
                'mttf': f"{server['mttf']:.2f}",
                'availability_percent': f"{server['availability_percent']:.2f}",
            })

    print(f"\nWyniki zapisane do plików {csv_filename_disks} i {csv_filename_servers}")

    # Построение графиков для дисков и серверов
    # Подготовка данных
    downtime_values_disks = [d[1]['downtime'] for d in all_disk_results]
    repair_cost_values_disks = [d[1]['repair_cost_total'] for d in all_disk_results]
    lost_revenue_values_disks = [d[1]['lost_revenue_total'] for d in all_disk_results]
    labels_disks = [d[0] for d in all_disk_results]

    downtime_values_servers = [s[1]['downtime'] for s in all_server_results]
    repair_cost_values_servers = [s[1]['repair_cost_total'] for s in all_server_results]
    lost_revenue_values_servers = [s[1]['lost_revenue'] for s in all_server_results]
    labels_servers = [s[0] for s in all_server_results]

    # Определение позиции для дисков и серверов
    num_disks = len(labels_disks)
    num_servers = len(labels_servers)
    x_disks = np.arange(num_disks)
    x_servers = np.arange(num_servers)

    # Создание фигуры с двумя столбцами
    fig, axes = plt.subplots(3, 2, figsize=(20, 15))

    # Метрики дисков
    # Czas przestoju dysków
    axes[0, 0].bar(x_disks, downtime_values_disks, color='tab:red')
    axes[0, 0].set_title('Czas przestoju dysków')
    axes[0, 0].set_ylabel('Godziny')
    axes[0, 0].set_xticks(x_disks)
    axes[0, 0].set_xticklabels(labels_disks, rotation=45, ha='right')

    # Koszty naprawy dysków
    axes[1, 0].bar(x_disks, repair_cost_values_disks, color='tab:blue')
    axes[1, 0].set_title('Koszty naprawy dysków')
    axes[1, 0].set_ylabel(f'Koszt ({currency})')
    axes[1, 0].set_xticks(x_disks)
    axes[1, 0].set_xticklabels(labels_disks, rotation=45, ha='right')

    # Utracone przychody z dysków
    axes[2, 0].bar(x_disks, lost_revenue_values_disks, color='tab:orange')
    axes[2, 0].set_title('Utracone przychody z dysków')
    axes[2, 0].set_ylabel(f'Kwota ({currency})')
    axes[2, 0].set_xticks(x_disks)
    axes[2, 0].set_xticklabels(labels_disks, rotation=45, ha='right')

    # Метрики серверов
    # Czas przestoju serwerów
    axes[0, 1].bar(x_servers, downtime_values_servers, color='tab:purple')
    axes[0, 1].set_title('Czas przestoju serwerów')
    axes[0, 1].set_ylabel('Godziny')
    axes[0, 1].set_xticks(x_servers)
    axes[0, 1].set_xticklabels(labels_servers, rotation=45, ha='right')

    # Koszty naprawy serwerów
    axes[1, 1].bar(x_servers, repair_cost_values_servers, color='tab:brown')
    axes[1, 1].set_title('Koszty naprawy serwerów')
    axes[1, 1].set_ylabel(f'Koszt ({currency})')
    axes[1, 1].set_xticks(x_servers)
    axes[1, 1].set_xticklabels(labels_servers, rotation=45, ha='right')

    # Utracone przychody serwerów
    axes[2, 1].bar(x_servers, lost_revenue_values_servers, color='tab:cyan')
    axes[2, 1].set_title('Utracone przychody serwerów')
    axes[2, 1].set_ylabel(f'Kwota ({currency})')
    axes[2, 1].set_xticks(x_servers)
    axes[2, 1].set_xticklabels(labels_servers, rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig('servers_disks_results.png')
    plt.show()


if __name__ == "__main__":
    main()
