# Railway System Maintenance Simulator

## 🚂 Overview

This project code is a simulation framework for analyzing the reliability and cost-effectiveness of different maintenance policies in a railway system. It calculates key metrics such as availability, downtime, maintenance costs, and reliability measures (MTBF, MTTR) by simulating the failure and repair process using a Weibull distribution. After running the simulations, the code saves the results to CSV and generates visual comparisons between policies.

## ✨ Features

- **Multiple Maintenance Policy Simulation:**
  - Preventive Maintenance
  - Reactive Maintenance
  - Predictive Maintenance

- **Comprehensive Analysis Metrics:**
  - System Availability
  - Mean Time Between Failures (MTBF)
  - Mean Time To Repair (MTTR)
  - Maintenance Costs
  - Component-specific failure rates
  - SLA compliance monitoring

- **Advanced Statistical Modeling:**
  - Weibull distribution for failure modeling
  - Monte Carlo simulation
  - Standard deviation analysis

- **Visualization and Reporting:**
  - Automated generation of comparative plots
  - CSV export functionality
  - Detailed logging system

## 🚀 Getting Started

### Prerequisites

```bash
pip install numpy matplotlib scipy
```

### Configuration

The simulator uses a JSON configuration file (`maintenance_policies.json`) to define:
- Simulation parameters
- SLA targets
- Maintenance policy specifications
- Component-specific details

Example configuration structure:
```json
{
    "simulation_duration": 10000,
    "num_simulations": 100,
    "sla_targets": {
        "availability": 0.975,
        "max_downtime": 700
    },
    "maintenance_policies": [
        {
            "name": "Preventive Maintenance",
            "avg_usage_time": 500,
            ...
        }
    ]
}
```

### Running the Simulator

```bash
python simulation.py
```

## 📊 Output

The simulator generates:

1. **CSV Results File** (`reliability_simulation_results.csv`):
   - Detailed metrics for each maintenance policy
   - Statistical analyses
   - SLA compliance status

2. **Visualization** (`maintenance_policy_comparison.png`):
   - Comparative bar charts for key metrics
   - System availability analysis
   - Cost comparison plots

## 📈 Sample Results

Based on the simulation results:

- **Predictive Maintenance** achieves the highest availability (97.73%) with minimal downtime
- **Preventive Maintenance** maintains good availability (94.99%) with moderate costs
- **Reactive Maintenance** shows higher costs and lower availability (85.00%)

## 🛠️ Technical Details

### Key Classes

- `RailwaySystemSimulator`: Main simulation engine
- `MaintenancePolicy`: Policy configuration handler
- `Component`: Component-level specification manager

### Simulation Methodology

1. Utilizes Weibull distribution for realistic failure modeling
2. Implements Monte Carlo simulation for statistical reliability
3. Considers component-level and system-level failures
4. Accounts for maintenance costs and repair times

## 📝 License

## 🤝 Developers

- **Oleksandr Radionenko**
- **Bohdan Stepanenko**
- **Mykhailo Dek**
