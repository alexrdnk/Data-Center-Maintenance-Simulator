import json
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
import csv
import heapq
from dataclasses import dataclass
from scipy.stats import weibull_min
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class Disk:
    model: str
    failure_rate: float
    repair_cost: float
    repair_time: float
    mttf: float


@dataclass
class Server:
    name: str
    availability_target: float
    avg_maintenance_cost: float
    avg_replacement_cost: float
    avg_service_cost: float
    repair_time: float
    raid_level: int
    number_of_disks: int
    disk_mttf: float


class DataCenterSimulator:
    def __init__(self, config_file: str):
        """
        Initialize the simulator with data center configuration
        """
        logging.info("Initializing data center simulator with configuration file: %s", config_file)
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Parse disks
        self.disks = {
            disk['model']: Disk(
                model=disk['model'],
                failure_rate=disk['failure_rate'],
                repair_cost=disk['repair_cost'],
                repair_time=disk['repair_time'],
                mttf=disk['mttf']
            ) for disk in config['disks']
        }

        # Parse servers
        self.servers = {
            server['name']: Server(
                name=server['name'],
                availability_target=server['availability_target'],
                avg_maintenance_cost=server['avg_maintenance_cost'],
                avg_replacement_cost=server['avg_replacement_cost'],
                avg_service_cost=server['avg_service_cost'],
                repair_time=server['repair_time'],
                raid_level=server['raid_level'],
                number_of_disks=server['number_of_disks'],
                disk_mttf=server['disk_mttf']
            ) for server in config['servers']
        }

        # Parse combinations and simulation parameters
        self.combinations = config['combinations']
        self.simulation_duration = config.get('simulation_duration', 10000)
        self.num_simulations = config.get('num_simulations', 100)
        self.sla_targets = config.get('sla_targets', {
            "availability": 0.99,
            "max_downtime": 5
        })

        logging.info("Simulator initialized with %d server-disk combinations.", len(self.combinations))

    @staticmethod
    def weibull_failure_time(shape: float, scale: float) -> float:
        """
        Simulate time to failure using Weibull distribution
        """
        return weibull_min.rvs(shape, scale=scale)

    def simulate_configuration(self, server: Server, disk: Disk) -> Dict[str, float]:
        """
        Simulate a single server and disk configuration
        """
        total_downtime = 0
        total_maintenance_cost = 0
        total_replacements = 0
        current_time = 0

        # Initialize disks with their time to failure
        disks = []
        for _ in range(server.number_of_disks):
            time_to_failure = current_time + self.weibull_failure_time(shape=1.5, scale=disk.mttf)
            disks.append({'failure_time': time_to_failure, 'failed': False})

        # Initialize variables to keep track of failed disks
        failed_disks = 0
        system_down = False
        downtime_start = None

        # Use a heap to manage events by time
        events = []

        # Schedule initial disk failures
        for i, disk_info in enumerate(disks):
            heapq.heappush(events, (disk_info['failure_time'], 'failure', i))

        while current_time < self.simulation_duration and events:
            # Get the next event
            event_time, event_type, disk_index = heapq.heappop(events)
            if event_time > self.simulation_duration:
                break
            current_time = event_time
            disk_info = disks[disk_index]

            if event_type == 'failure':
                # Disk fails
                disk_info['failed'] = True
                failed_disks += 1
                # Check if system is still operational based on RAID level
                system_failed = False
                if server.raid_level == 0:
                    system_failed = True
                elif server.raid_level == 1:
                    if failed_disks == server.number_of_disks:
                        system_failed = True
                elif server.raid_level == 5:
                    if failed_disks > 1:
                        system_failed = True
                elif server.raid_level == 6:
                    if failed_disks > 2:
                        system_failed = True

                if system_failed and not system_down:
                    # System goes down
                    system_down = True
                    downtime_start = current_time

                # Schedule repair
                repair_time = current_time + disk.repair_time
                heapq.heappush(events, (repair_time, 'repair', disk_index))

                total_maintenance_cost += server.avg_service_cost + server.avg_maintenance_cost + disk.repair_cost
                total_replacements += 1

            elif event_type == 'repair':
                # Disk is repaired
                disk_info['failed'] = False
                failed_disks -= 1

                # Calculate downtime for repair
                if system_down:
                    system_recovered = False
                    print(server.raid_level)
                    if server.raid_level == 0 or (server.raid_level == 1 and failed_disks < server.number_of_disks) or \
                            (server.raid_level == 5 and failed_disks <= 1) or (
                            server.raid_level == 6 and failed_disks <= 2):
                        system_recovered = True

                    if system_recovered:
                        # System comes back up
                        system_down = False
                        downtime_end = current_time
                        print(downtime_end)
                        downtime_duration = downtime_end - downtime_start
                        total_downtime += downtime_duration
                        downtime_start = None

                # Schedule next failure for this disk
                time_to_failure = current_time + self.weibull_failure_time(shape=1.5, scale=disk.mttf)
                disk_info['failure_time'] = time_to_failure
                heapq.heappush(events, (disk_info['failure_time'], 'failure', disk_index))

        # If system is down at the end of simulation, account for remaining downtime
        if system_down:
            downtime_end = self.simulation_duration
            downtime_duration = downtime_end - downtime_start

            total_downtime += downtime_duration

        # After the simulation, calculate metrics
        total_time = self.simulation_duration
        uptime = total_time - total_downtime
        availability = (uptime / total_time) * 100
        MTBF = uptime / total_replacements if total_replacements > 0 else float('inf')
        MTTR = server.repair_time / total_replacements if total_replacements > 0 else 0

        return {
            'server_name': server.name,
            'disk_model': disk.model,
            'total_downtime': total_downtime,
            'total_maintenance_cost': total_maintenance_cost,
            'total_replacements': total_replacements,
            'availability': availability,
            'MTBF': MTBF,
            'MTTR': MTTR  # This is where MTTR is calculated
        }

    def run_simulations(self) -> List[Dict[str, float]]:
        """
        Run multiple simulations for each server-disk combination
        """
        all_results = []
        logging.info("Starting simulations...")

        for combination in self.combinations:
            server = self.servers[combination['server']]
            disk = self.disks[combination['disk']]

            logging.info(f"Simulating server {server.name} with disk {disk.model}")

            # Run multiple simulations for this configuration
            config_results = [
                self.simulate_configuration(server, disk)
                for _ in range(self.num_simulations)
            ]

            # Aggregate results
            aggregated_results = {
                'server_name': server.name,
                'disk_model': disk.model,
                'avg_downtime': np.mean([r['total_downtime'] for r in config_results]),
                'avg_maintenance_cost': np.mean([r['total_maintenance_cost'] for r in config_results]),
                'avg_replacements': np.mean([r['total_replacements'] for r in config_results]),
                'avg_availability': np.mean([r['availability'] for r in config_results]),
                'avg_MTBF': np.mean([r['MTBF'] for r in config_results]),
                'avg_MTTR': np.mean([r['MTTR'] for r in config_results]),
                'meets_sla': (
                        np.mean([r['availability'] for r in config_results]) >= server.availability_target
                ),
                'std_downtime': np.std([r['total_downtime'] for r in config_results]),
                'std_maintenance_cost': np.std([r['total_maintenance_cost'] for r in config_results])
            }

            all_results.append(aggregated_results)

        logging.info("Simulations completed.")
        return all_results

    @staticmethod
    def save_results_to_csv(results: List[Dict[str, float]], filename: str = 'data_center_simulation_results.csv'):
        """
        Save simulation results to CSV
        """
        logging.info("Saving results to CSV: %s", filename)
        # Define the header with necessary columns
        keys = [
            'server_name',
            'disk_model',
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

        # Write to CSV file
        with open(filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()

            for result in results:
                dict_writer.writerow(result)

        logging.info("Results successfully saved to %s", filename)

    @staticmethod
    def plot_results(results: List[Dict[str, float]]):
        """
        Create visualizations of simulation results and save as a PNG file.
        """
        logging.info("Generating plots...")

        # Prepare data for plotting
        servers = list(set(r['server_name'] for r in results))
        disks = list(set(r['disk_model'] for r in results))

        # Create a large figure for all subplots
        plt.figure(figsize=(15, 12))

        # Maintenance Cost plot
        plt.subplot(2, 2, 1)
        for server in servers:
            server_results = [r for r in results if r['server_name'] == server]
            plt.bar(
                [f"{r['server_name']}-{r['disk_model']}" for r in server_results],
                [r['avg_maintenance_cost'] for r in server_results]
            )
        plt.title('Average Maintenance Cost')
        plt.ylabel('Cost')
        plt.xticks(rotation=45, ha='right')

        # MTTR plot (instead of Downtime plot)
        plt.subplot(2, 2, 2)
        for server in servers:
            server_results = [r for r in results if r['server_name'] == server]
            plt.bar(
                [f"{r['server_name']}-{r['disk_model']}" for r in server_results],
                [r['avg_MTTR'] for r in server_results]  # Changed to MTTR
            )
        plt.title('Average MTTR (Mean Time to Repair)')
        plt.ylabel('MTTR (hours)')
        plt.xticks(rotation=45, ha='right')

        # MTBF plot
        plt.subplot(2, 2, 4)
        for server in servers:
            server_results = [r for r in results if r['server_name'] == server]
            plt.bar(
                [f"{r['server_name']}-{r['disk_model']}" for r in server_results],
                [r['avg_MTBF'] for r in server_results]
            )
        plt.title('Mean Time Between Failures (MTBF)')
        plt.ylabel('MTBF (hours)')
        plt.xticks(rotation=45, ha='right')

        # Replacements plot
        plt.subplot(2, 2, 3)
        for server in servers:
            server_results = [r for r in results if r['server_name'] == server]
            plt.bar(
                [f"{r['server_name']}-{r['disk_model']}" for r in server_results],
                [r['avg_replacements'] for r in server_results]
            )
        plt.title('Average Disk Replacements')
        plt.ylabel('Replacements')
        plt.xticks(rotation=45, ha='right')

        # Adjust layout to prevent overlapping
        plt.tight_layout()

        # Save the plot to a PNG file
        plt.savefig('data_center_policy_comparison.png', format='png')

        # Close the plot to free memory
        plt.close()

        logging.info("Plots generated and saved to data_center_policy_comparison.png")

    @staticmethod
    def run_and_save(config_file: str, output_file: str = 'data_center_simulation_results.csv'):
        """
        A wrapper method to run simulations and save the results to a CSV file.
        """
        # Initialize the simulator with the provided config file
        simulator = DataCenterSimulator(config_file)

        # Run the simulations
        results = simulator.run_simulations()

        # Save results to CSV
        simulator.save_results_to_csv(results, output_file)

        # Generate and display plots
        simulator.plot_results(results)

        logging.info("Simulation complete and results saved.")

# Example usage:
if __name__ == "__main__":
    # Specify the config file path (for example, 'data_center_config.json')
    config_file = 'data_center_config.json'
    # Run the simulation and save results to CSV
    DataCenterSimulator.run_and_save(config_file)
