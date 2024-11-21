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
class MaintenancePolicy:
    name: str
    avg_usage_time: float
    avg_maintenance_cost: float
    avg_replacement_cost: float
    avg_service_cost: float
    failure_rate: float
    repair_time: float
    components: List[Component] = None

class RailwaySystemSimulator:
    def __init__(self, config_file: str):
        """
        Initialize the simulator with maintenance policy configurations
        """
        logging.info("Initializing simulator with configuration file: %s", config_file)
        with open(config_file, 'r') as f:
            config = json.load(f)

        self.policies = [
            MaintenancePolicy(
                name=policy['name'],
                avg_usage_time=policy['avg_usage_time'],
                avg_maintenance_cost=policy['avg_maintenance_cost'],
                avg_replacement_cost=policy['avg_replacement_cost'],
                avg_service_cost=policy['avg_service_cost'],
                failure_rate=policy['failure_rate'],
                repair_time=policy['repair_time'],
                components=[
                    Component(
                        name=comp['name'],
                        failure_rate=comp['failure_rate'],
                        repair_time=comp['repair_time']
                    ) for comp in policy.get('components', [])
                ]
            ) for policy in config['maintenance_policies']
        ]

        self.simulation_duration = config.get('simulation_duration', 10000)
        self.num_simulations = config.get('num_simulations', 100)
        self.sla_targets = config.get('sla_targets', {
            "availability": 0.99,
            "max_downtime": 500
        })

        logging.info("Simulator initialized with %d policies.", len(self.policies))

    @staticmethod
    def weibull_failure_time(shape: float, scale: float) -> float:
        """
        Simulate time to failure using Weibull distribution
        """
        return weibull_min.rvs(shape, scale=scale)

    def simulate_policy(self, policy: MaintenancePolicy) -> Dict[str, float]:
        """
        Simulate a single maintenance policy
        """
        total_downtime = 0
        total_maintenance_cost = 0
        total_replacements = 0
        current_time = 0

        while current_time < self.simulation_duration:
            # Time until next failure using Weibull distribution for aging
            time_to_failure = self.weibull_failure_time(shape=1.5, scale=policy.avg_usage_time)
            current_time += time_to_failure

            if current_time < self.simulation_duration:
                # Failure occurs
                total_downtime += policy.repair_time
                total_maintenance_cost += policy.avg_service_cost + policy.avg_maintenance_cost
                total_replacements += 1

        MTBF = self.simulation_duration / total_replacements if total_replacements > 0 else float('inf')
        MTTR = total_downtime / total_replacements if total_replacements > 0 else 0
        availability = (MTBF / (MTBF + MTTR)) * 100 if MTBF + MTTR > 0 else 100

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
        Run multiple simulations for each maintenance policy
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
                            filename: str = 'reliability_simulation_results.csv'):
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
        plt.title('Average Replacements')
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
        plt.savefig('maintenance_policy_comparison.png')
        plt.close()

        logging.info("Plots generated and saved to 'maintenance_policy_comparison.png'.")


def main():
    logging.info("Starting the program...")
    simulator = RailwaySystemSimulator('maintenance_policies.json')
    results = simulator.run_simulations()
    simulator.save_results_to_csv(results)
    simulator.plot_results(results)
    logging.info("Program completed successfully.")


if __name__ == "__main__":
    main()