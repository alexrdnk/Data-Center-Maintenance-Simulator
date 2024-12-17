import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import weibull_min
import csv
import random


def simulate_disk(sim_duration, repair_cost, lost_revenue_per_hour, shape, seed):
    random.seed(seed)
    np.random.seed(seed)

    current_time = 0.0
    total_downtime = 0.0
    total_repairs = 0

    scale_for_weibull = sim_duration / 2.0

    failure_time = weibull_min.rvs(shape, scale=scale_for_weibull)

    while current_time < sim_duration:
        if failure_time > sim_duration:
            # Нет больше отказов
            break

        # Отказ
        current_time = failure_time
        downtime_start = current_time
        total_repairs += 1

        repair_time = 2.0
        repair_finish = current_time + repair_time
        if repair_finish > sim_duration:
            repair_finish = sim_duration

        downtime = repair_finish - downtime_start
        total_downtime += downtime
        current_time = repair_finish

        # Следующий отказ
        failure_time = current_time + weibull_min.rvs(shape, scale=scale_for_weibull)

    # Итоговый расчет MTTF и MTTR
    if total_repairs > 0:
        mttr = total_downtime / total_repairs
        mttf = sim_duration / total_repairs
    else:
        mttr = 0.0
        mttf = sim_duration

    repair_cost_total = total_repairs * repair_cost
    lost_revenue_total = total_downtime * lost_revenue_per_hour
    availability_percent = (mttf/(mttf+mttr)) * 100.0

    return {
        'downtime': total_downtime,
        'repairs': total_repairs,
        'repair_cost_total': repair_cost_total,
        'lost_revenue_total': lost_revenue_total,
        'mttr': mttr,
        'mttf': mttf,
        'availability_percent': availability_percent
    }


def main():
    with open('config.json', 'r') as f:
        config = json.load(f)

    sim_duration = config['time_period_hours']
    shape = config['weibull_shape']
    currency = config['currency']

    results = []
    labels = []

    # Теперь MTTF/MTTR не берутся из конфига, для ремонта мы использовали фиктивное значение 2.0 ч в simulate_disk.
    # Если у нас есть разные repair_cost и lost_revenue_per_hour в конфиге, используем их.
    for server in config['servers']:
        server_id = server['id']
        for disk_id, disk_params in enumerate(server['disks'], start=1):
            seed = server_id * 100 + disk_id
            repair_cost = disk_params['repair_cost_PLN']
            lost_revenue_per_hour = disk_params['lost_revenue_per_hour_PLN']

            res = simulate_disk(sim_duration, repair_cost, lost_revenue_per_hour, shape, seed)
            results.append(res)
            labels.append(f"S{server_id}D{disk_id}")

    downtime_values = [r['downtime'] for r in results]
    repair_cost_values = [r['repair_cost_total'] for r in results]
    lost_revenue_values = [r['lost_revenue_total'] for r in results]
    mttr_values = [r['mttr'] for r in results]
    mttf_values = [r['mttf'] for r in results]
    availability_values = [r['availability_percent'] for r in results]

    print("Wyniki symulacji:")
    for i, label in enumerate(labels):
        print(f"{label}: Przestój={downtime_values[i]:.2f}h, Koszt naprawy={repair_cost_values[i]:.2f}{currency}, "
              f"Utracone przychody={lost_revenue_values[i]:.2f}{currency}, Dostępność={availability_values[i]:.2f}%, "
              f"MTTR={mttr_values[i]:.2f}h, MTTF={mttf_values[i]:.2f}h")

    # Zapis do CSV
    csv_filename = 'results.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['server_disk', 'downtime_hours', 'repair_cost', 'lost_revenue', 'availability_percent', 'mttr',
                      'mttf']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i, label in enumerate(labels):
            writer.writerow({
                'server_disk': label,
                'downtime_hours': round(downtime_values[i], 2),
                'repair_cost': round(repair_cost_values[i], 2),
                'lost_revenue': round(lost_revenue_values[i], 2),
                'availability_percent': round(availability_values[i], 2),
                'mttr': round(mttr_values[i], 2),
                'mttf': round(mttf_values[i], 2),
            })

    print(f"Wyniki zapisane do pliku {csv_filename}")

    # Tworzenie wykresów
    x = np.arange(len(labels))
    fig, axes = plt.subplots(4, 1, figsize=(10, 14))

    axes[0].bar(x, downtime_values, color='tab:red')
    axes[0].set_title('Czas przestoju')
    axes[0].set_ylabel('Godziny')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels)

    axes[1].bar(x, repair_cost_values, color='tab:blue')
    axes[1].set_title('Koszty naprawy')
    axes[1].set_ylabel(f'Koszt ({currency})')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels)

    axes[2].bar(x, lost_revenue_values, color='tab:orange')
    axes[2].set_title('Utracone przychody')
    axes[2].set_ylabel(f'Kwota ({currency})')
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(labels)

    axes[3].bar(x, availability_values, color='tab:green')
    axes[3].set_title('Dostępność (%)')
    axes[3].set_ylabel('Procent')
    axes[3].set_xticks(x)
    axes[3].set_xticklabels(labels)

    plt.tight_layout()
    plt.savefig('servers_disks_results.png')
    plt.show()


if __name__ == "__main__":
    main()
