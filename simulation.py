import json
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
import csv
from dataclasses import dataclass
from scipy.stats import weibull_min
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class Component:
    name: str
    failure_rate: float
    repair_time: float

@dataclass
class DataCenterPolicy:
    name: str
    avg_maintenance_cost: float
    avg_replacement_cost: float
    avg_service_cost: float
    repair_time: float
    raid_level: int
    number_of_disks: int
    disk_mttf: float
    components: List[Component] = None

class RailwaySystemSimulator:
    def __init__(self, config_file: str):
        """
         Initialize the simulator with data center policy configurations
        """
        logging.info("Initializing data center simulator with configuration file: %s", config_file)
        with open(config_file, 'r') as f:
            config = json.load(f)

        self.policies = [
            DataCenterPolicy(
                name=policy['name'],
                avg_maintenance_cost=policy['avg_maintenance_cost'],
                avg_replacement_cost=policy['avg_replacement_cost'],
                avg_service_cost=policy['avg_service_cost'],
                repair_time=policy['repair_time'],
                raid_level=policy['raid_level'],
                number_of_disks=policy['number_of_disks'],
                disk_mttf=policy['disk_mttf'],
                components=[
                    Component(
                        name=comp['name'],
                        failure_rate=comp['failure_rate'],
                        repair_time=comp['repair_time']
                    ) for comp in policy.get('components', [])
                ]
            ) for policy in config['data_center_policies']
        ]

        self.simulation_duration = config.get('simulation_duration', 10000)
        self.num_simulations = config.get('num_simulations', 100)
        self.sla_targets = config.get('sla_targets', {
            "availability": 99.99,
            "max_downtime": 5
        })

        logging.info("Simulator initialized with %d data center policies.", len(self.policies))

    @staticmethod
    def weibull_failure_time(shape: float, scale: float) -> float:
        """
        Simulate time to failure using Weibull distribution
        """
        return weibull_min.rvs(shape, scale=scale)

    def simulate_policy(self, policy: DataCenterPolicy) -> Dict[str, float]:
        """
        Simulate a single data center policy
        """
        total_downtime = 0
        total_maintenance_cost = 0
        total_replacements = 0
        current_time = 0

        # Initialize disks with their time to failure
        disks = []
        for _ in range(policy.number_of_disks):
            time_to_failure = current_time + self.weibull_failure_time(shape=1.5, scale=policy.disk_mttf)
            disks.append({'failure_time': time_to_failure, 'failed': False})

        # Initialize variables to keep track of failed disks
        failed_disks = 0
        system_down = False
        downtime_start = None

        # Events will be the times when disks fail or are repaired
        events = []

        # Schedule initial disk failures
        for i, disk in enumerate(disks):
            events.append((disk['failure_time'], 'failure', i))

        # Sort events by time
        events.sort()

        while current_time < self.simulation_duration and events:
            # Get the next event
            event_time, event_type, disk_index = events.pop(0)
            if event_time > self.simulation_duration:
                break
            current_time = event_time
            disk = disks[disk_index]

            if event_type == 'failure':
                # Disk fails
                disk['failed'] = True
                failed_disks += 1
                # Check if system is still operational based on RAID level
                system_failed = False
                if policy.raid_level == 0:
                    # RAID 0: any disk failure causes system failure
                    system_failed = True
                elif policy.raid_level == 1:
                    # RAID 1: system fails only if all disks fail
                    if failed_disks == policy.number_of_disks:
                        system_failed = True
                elif policy.raid_level == 5:
                    # RAID 5: system fails if more than one disk fails
                    if failed_disks > 1:
                        system_failed = True
                elif policy.raid_level == 6:
                    # RAID 6: system fails if more than two disks fail
                    if failed_disks > 2:
                        system_failed = True
                else:
                    # For other RAID levels, assume no redundancy
                    system_failed = True

                if system_failed and not system_down:
                    # System goes down
                    system_down = True
                    downtime_start = current_time

                # Schedule repair
                repair_time = current_time + policy.repair_time
                events.append((repair_time, 'repair', disk_index))
                events.sort()

                total_maintenance_cost += policy.avg_service_cost + policy.avg_maintenance_cost
                total_replacements += 1

            elif event_type == 'repair':
                # Disk is repaired
                disk['failed'] = False
                failed_disks -= 1

                # Check if system can come back up
                if system_down:
                    system_recovered = False
                    if policy.raid_level == 0:
                        # RAID 0: system can come back up after repair
                        system_recovered = True
                    elif policy.raid_level == 1:
                        # RAID 1: system is up if at least one disk is operational
                        if failed_disks < policy.number_of_disks:
                            system_recovered = True
                    elif policy.raid_level == 5:
                        # RAID 5: system is up if failed disks <= 1
                        if failed_disks <= 1:
                            system_recovered = True
                    elif policy.raid_level == 6:
                        # RAID 6: system is up if failed disks <= 2
                        if failed_disks <= 2:
                            system_recovered = True
                    else:
                        # For other RAID levels, assume no redundancy
                        system_recovered = False

                    if system_recovered:
                        # System comes back up
                        system_down = False
                        downtime_end = current_time
                        total_downtime += downtime_end - downtime_start
                        downtime_start = None

                # Schedule next failure for this disk
                time_to_failure = current_time + self.weibull_failure_time(shape=1.5, scale=policy.disk_mttf)
                disk['failure_time'] = time_to_failure
                events.append((disk['failure_time'], 'failure', disk_index))
                events.sort()

        # If system is down at the end of simulation, account for remaining downtime
        if system_down:
            downtime_end = self.simulation_duration
            total_downtime += downtime_end - downtime_start

        # After the simulation, calculate metrics
        total_time = self.simulation_duration
        uptime = total_time - total_downtime
        availability = (uptime / total_time) * 100
        MTBF = uptime / total_replacements if total_replacements > 0 else float('inf')
        MTTR = total_downtime / total_replacements if total_replacements > 0 else 0

        return {
            'policy_name': policy.name,
            'total_downtime': total_downtime,
            'total_maintenance_cost': total_maintenance_cost,
            'total_replacements': total_replacements,
            'availability': availability,
            'MTBF': MTBF,
            'MTTR': MTTR
        }

    def run_simulations(self) -> List[Dict[str, float]]:
        """
        Run multiple simulations for each data center policy
        """
        all_results = []
        logging.info("Starting simulations...")

        for policy in self.policies:
            logging.info("Simulating policy: %s", policy.name)
            policy_results = [
                self.simulate_policy(policy)
                for _ in range(self.num_simulations)
            ]

            # Aggregate results
            aggregated_results = {
                'policy_name': policy.name,
                'avg_downtime': np.mean([r['total_downtime'] for r in policy_results]),
                'avg_maintenance_cost': np.mean([r['total_maintenance_cost'] for r in policy_results]),
                'avg_replacements': np.mean([r['total_replacements'] for r in policy_results]),
                'avg_availability': np.mean([r['availability'] for r in policy_results]),
                'avg_MTBF': np.mean([r['MTBF'] for r in policy_results]),
                'avg_MTTR': np.mean([r['MTTR'] for r in policy_results]),
                'meets_sla': (
                    np.mean([r['availability'] for r in policy_results]) >= self.sla_targets['availability'] and
                    np.mean([r['total_downtime'] for r in policy_results]) <= self.sla_targets['max_downtime']
                ),
                'std_downtime': np.std([r['total_downtime'] for r in policy_results]),
                'std_maintenance_cost': np.std([r['total_maintenance_cost'] for r in policy_results])
            }

            all_results.append(aggregated_results)

        logging.info("Simulations completed.")
        return all_results

    @staticmethod
    def save_results_to_csv(results: List[Dict[str, float]],
                            filename: str = 'data_center_simulation_results.csv'):
        """
        Save simulation results to CSV in a formatted table style.
        Each result will be represented in a row with clear column names.
        """

        logging.info("Saving results to CSV: %s", filename)
        # Define the header with necessary columns
        keys = [
            'policy_name',
            'avg_downtime',
            'avg_maintenance_cost',
            'avg_replacements',
            'avg_availability',
            'avg_MTBF',
            'avg_MTTR',
            'std_downtime',
            'std_maintenance_cost',
            'meets_sla'
        ]

        # Extracting component-specific data (if any)
        component_names = set()
        for result in results:
            for component, failures in result.get('component_failures', {}).items():
                component_names.add(component)

        # Create column names for each component's failure and downtime data
        for component in component_names:
            keys.append(f'component_{component}_failures')
            keys.append(f'component_{component}_downtime')

        # Write to CSV file
        with open(filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()

            for result in results:
                # Prepare a row with general data
                row = {
                    'policy_name': result['policy_name'],
                    'avg_downtime': round(result['avg_downtime'], 2),
                    'avg_maintenance_cost': round(result['avg_maintenance_cost'], 2),
                    'avg_replacements': result['avg_replacements'],
                    'avg_availability': round(result['avg_availability'], 4),
                    'avg_MTBF': round(result['avg_MTBF'], 2),
                    'avg_MTTR': round(result['avg_MTTR'], 2),
                    'std_downtime': round(result['std_downtime'], 2),
                    'std_maintenance_cost': round(result['std_maintenance_cost'], 2),
                    'meets_sla': result['meets_sla']
                }

                # Add component-specific failure and downtime data
                for component in component_names:
                    row[f'component_{component}_failures'] = result['component_failures'].get(component, 0)
                    row[f'component_{component}_downtime'] = round(result['component_downtime'].get(component, 0), 2)

                dict_writer.writerow(row)

        logging.info("Results saved to CSV.")

    @staticmethod
    def plot_results(results: List[Dict[str, float]]):
        """
        Create visualizations of simulation results
        """
        logging.info("Generating plots...")
        plt.figure(figsize=(15, 10))

        # Availability plot
        plt.subplot(3, 2, 1)
        plt.bar(
            [r['policy_name'] for r in results],
            [r['avg_availability'] for r in results]
        )
        plt.title('Average System Availability')
        plt.ylabel('Availability')
        plt.xticks(rotation=45)

        # Maintenance Cost plot
        plt.subplot(3, 2, 2)
        plt.bar(
            [r['policy_name'] for r in results],
            [r['avg_maintenance_cost'] for r in results]
        )
        plt.title('Average Maintenance Cost')
        plt.ylabel('Cost')
        plt.xticks(rotation=45)

        # Downtime plot
        plt.subplot(3, 2, 3)
        plt.bar(
            [r['policy_name'] for r in results],
            [r['avg_downtime'] for r in results]
        )
        plt.title('Average Downtime')
        plt.ylabel('Downtime')
        plt.xticks(rotation=45)

        # Replacements plot
        plt.subplot(3, 2, 4)
        plt.bar(
            [r['policy_name'] for r in results],
            [r['avg_replacements'] for r in results]
        )
        plt.title('Average Disk Replacements')
        plt.ylabel('Number of Replacements')
        plt.xticks(rotation=45)

        # MTBF plot
        plt.subplot(3, 2, 5)
        plt.bar(
            [r['policy_name'] for r in results],
            [r['avg_MTBF'] for r in results]
        )
        plt.title('Mean Time Between Failures (MTBF)')
        plt.ylabel('MTBF')
        plt.xticks(rotation=45)

        # MTTR plot
        plt.subplot(3, 2, 6)
        plt.bar(
            [r['policy_name'] for r in results],
            [r['avg_MTTR'] for r in results]
        )
        plt.title('Mean Time To Repair (MTTR)')
        plt.ylabel('MTTR')
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig('data_center_policy_comparison.png')
        plt.close()

        logging.info("Plots generated and saved to 'data_center_policy_comparison.png'.")


def main():
    logging.info("Starting the data center simulation program...")
    simulator = RailwaySystemSimulator('data_center_policies.json')
    results = simulator.run_simulations()
    simulator.save_results_to_csv(results)
    simulator.plot_results(results)
    logging.info("Program completed successfully.")


if __name__ == "__main__":
    main()