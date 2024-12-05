# Railway System Maintenance Simulator

## 🚂 Overview

This project code is a simulation framework for analyzing the reliability and cost-effectiveness of different maintenance policies in a railway system. It calculates key metrics such as availability, downtime, maintenance costs, and reliability measures (MTBF, MTTR) by simulating the failure and repair process using a Weibull distribution. After running the simulations, the code saves the results to CSV and generates visual comparisons between policies.

## ✨ Features

- **Multiple RAID Configuration Simulation:**
  - RAID 0
  - RAID 1
  - RAID 5
  - RAID 6

- **Comprehensive Analysis Metrics:**
  - System Availability
  - Mean Time Between Failures (MTBF)
  - Mean Time To Repair (MTTR)
  - Maintenance Costs
  - Disk Failure Rate
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
- Ensure you have following Python libraries installed:
```bash
pip install numpy matplotlib scipy
```

### Configuration

The simulator uses a JSON configuration file (`data_center_policies.json`) to define:
- Simulation parameters
- SLA targets
- Data center policy specifications
- Disk and RAID configurations

Example configuration structure:
```json
{
    "simulation_duration": 10000,
    "num_simulations": 100,
    "sla_targets": {
        "availability": 99.99,
        "max_downtime": 5
    },
    "data_center_policies": [
        {
            "name": "Policy_RAID0",
            "avg_maintenance_cost": 1000,
            "avg_replacement_cost": 5000,
            "avg_service_cost": 2000,
            "repair_time": 10,
            "raid_level": 0,
            "number_of_disks": 5,
            "disk_mttf": 1000
        },
        {
            "name": "Policy_RAID1",
            "avg_maintenance_cost": 2000,
            "avg_replacement_cost": 6000,
            "avg_service_cost": 2500,
            "repair_time": 10,
            "raid_level": 1,
            "number_of_disks": 2,
            "disk_mttf": 1000
        },
        {
            "name": "Policy_RAID5",
            "avg_maintenance_cost": 3000,
            "avg_replacement_cost": 7000,
            "avg_service_cost": 3000,
            "repair_time": 15,
            "raid_level": 5,
            "number_of_disks": 5,
            "disk_mttf": 1000
        },
        {
            "name": "Policy_RAID6",
            "avg_maintenance_cost": 4000,
            "avg_replacement_cost": 8000,
            "avg_service_cost": 3500,
            "repair_time": 20,
            "raid_level": 6,
            "number_of_disks": 6,
            "disk_mttf": 1000
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

1. **CSV Results File** (`data_center_simulation_results.csv`):
   - Detailed metrics for each maintenance policy
   - Statistical analyses
   - SLA compliance status

2. **Visualization** (`data_center_policy_comparison.png`):
   - Comparative bar charts for key metrics
   - System availability analysis
   - Cost comparison plots

## 📈 Sample Results

Based on the simulation results:

- **RAID 6 Configuration:** **Very high availability** (99.98%) and **low downtime** (1.99 hours) at the **highest cost** (482,100 units). Strong fault tolerance (MTTR: 0.03 hours) but reduced reliability (MTBF: 156.7 hours). Best for systems requiring redundancy.
- **RAID 5 Configuration:** **Good availability** (99.75%) and moderate downtime (25.04 hours) but **high costs** (319,380 units). Balanced reliability (MTBF: 189.7 hours, MTTR: 0.47 hours) but limited fault tolerance.
- **RAID 1 Configuration:** **Highest availability** (99.99%) and **minimal downtime** (1.28 hours) with relatively low costs (95,490 units). Excellent reliability (MTBF: 483.08 hours, MTTR: 0.06 hours). Suitable for highly reliable systems.
- **RAID 0 Configuration:** **Lowest availability** (94.90%) and **high downtime** (509.75 hours) with moderate costs (159,840 units). Poor reliability with frequent failures (MTBF: 179.61 hours, MTTR: 9.57 hours). Not recommended for critical systems.


## 🛠️ Technical Details

### Key Classes

- `DataCenterSimulator`: Main simulation engine
- `DataCenterPolicy`: Policy configuration handler
- `Component`: Component-level specification manager

### Simulation Methodology

1. **Failure Modeling**: Utilizes the Weibull distribution for realistic disk failure modeling.
2. **Monte Carlo Simulation**: Implements Monte Carlo simulation for statistical reliability.
3. **RAID Logic**:
- **RAID 0**: Any disk failure causes system failure.
- **RAID 1**: System operates as long as at least one disk is functional.
- **RAID 5**: System can tolerate the failure of one disk.
- **RAID 6**: System can tolerate the failure of two disks.
- **RAID 10/50/60**: Combinations of different RAID levels with advanced redundancy.
4. **Maintenance Costs and Repair Times**: Accounts for maintnenance costs and the time required for restore the system.



## 📝 License

## 🤝 Developers

- **Oleksandr Radionenko**
- **Bohdan Stepanenko**
- **Mykhailo Dek**
