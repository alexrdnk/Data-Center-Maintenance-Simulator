# Symulator Utrzymania Systemu Kolejowego
## 🚂 Przegląd
Ten projekt to framework symulacyjny zaprojektowany do analizy niezawodności i opłacalności różnych konfiguracji centrów danych, ze szczególnym uwzględnieniem konfiguracji dysków RAID i ich wpływu na dostępność systemu. Oblicza kluczowe metryki, takie jak dostępność, czas przestoju, koszty utrzymania oraz miary niezawodności (MTBF, MTTR) poprzez symulację procesów awarii i naprawy z wykorzystaniem rozkładu Weibulla. Po przeprowadzeniu symulacji kod zapisuje wyniki do pliku CSV i generuje wizualne porównania między różnymi konfiguracjami RAID.
## ✨ Funkcje
- **Symulacja Wielu Konfiguracji RAID:**
  - RAID 0
  - RAID 1
  - RAID 5
  - RAID 6
- **Kompleksowe Wskaźniki Analizy:**
  - Dostępność Systemu
  - Średni Czas Między Awariami (MTBF)
  - Średni Czas Do Naprawy (MTTR)
  - Koszty Utrzymania
  - Wskaźniki awaryjności dysków
  - Monitorowanie zgodności z SLA
- **Zaawansowane Modelowanie Statystyczne:**
  - Rozkład Weibulla do modelowania awarii
  - Symulacja Monte Carlo
  - Analiza odchylenia standardowego
- **Wizualizacja i Raportowanie:**
  - Automatyczne generowanie wykresów porównawczych
  - Funkcjonalność eksportu do CSV
  - Szczegółowy system logowania

## 🚀 Rozpoczęcie Pracy
### Wymagania Wstępne
- Upewnij się, że masz zainstalowane następujące biblioteki Pythona:
```bash
pip install numpy matplotlib scipy
```

### Konfiguracja
Symulator wykorzystuje plik konfiguracyjny JSON (`data_center_policies.json`) do zdefiniowania:
- Parametrów symulacji
- Celów SLA
- Specyfikacji polityk serwerowni
- Konfiguracji dysków i RAID

Przykładowa struktura konfiguracji:
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

### Uruchamianie Symulatora
```bash
python data_center_simulator.py
```

## 📊 Wyniki
Symulator generuje:
1. **Plik CSV z Wynikami** (`data_center_simulation_results.csv`):
   - Szczegółowe wskaźniki dla każdej polityki serwerowni
   - Analizy statystyczne
   - Status zgodności z SLA
2. **Wizualizacja** (`data_center_policy_comparison.png`):
   - Porównawcze wykresy słupkowe dla kluczowych wskaźników
   - Analiza dostępności systemu
   - Wykresy porównania kosztów

## 📈 Przykładowe Wyniki
Na podstawie wyników symulacji:
- **Konfiguracja RAID 6:** **Bardzo wysoka dostępność** (99,97%) i **niski czas przestoju** (2,55 godziny), ale **przy najwyższych kosztach** (478 950 jednostek). Zapewnia wysoką tolerancję na awarie (MTTR: 0,04 godziny), ale ma krótszy czas między awariami (MTBF: 157,75 godzin). Idealny dla systemów, które priorytetowo traktują redundancję.
- **Konfiguracja RAID 5:** **Dobra dostępność** (99,77%) i niski czas przestoju (23,37 godziny), ale **wysokie koszty utrzymania** (315 240 jednostek). Niezawodność na średnim poziomie (MTBF: 191,62 godzin, MTTR: 0,44 godziny), co czyni go zrównoważonym wyborem pod względem kosztów i dostępności.
- **Konfiguracja RAID 1:** **Najwyższa dostępność** (99,99%) i **minimalny czas przestoju** (1,2 godziny) przy najniższych kosztach (94 725 jednostek). Doskonała niezawodność z najdłuższym czasem między awariami (MTBF: 486,25 godzin) i najkrótszym czasem naprawy (MTTR: 0,06 godziny). Najlepszy wybór dla systemów wymagających wysokiej niezawodności.
- **Konfiguracja RAID 0:** **Najniższa dostępność** (94,91%) i **największy czas przestoju** (509,12 godzin) przy umiarkowanych kosztach (159 660 jednostek). Niska niezawodność z powodu częstych awarii (MTBF: 180,07 godzin, MTTR: 9,57 godzin). Najmniej odpowiedni dla systemów krytycznych.
## 🛠️ Szczegóły Techniczne
### Kluczowe Klasy
- `DataCenterSimulator`: Główny silnik symulacji
- `DataCenterPolicy`: Obsługa konfiguracji polityk
- `Component`: Menedżer specyfikacji na poziomie komponentów

### Metodologia Symulacji
1.  **Modelowanie Awarii:** Wykorzystuje rozkład Weibulla do realistycznego modelowania awarii
2. **Symulacja Monte Carlo** Implementuje symulację Monte Carlo dla niezawodności statystycznej
3. **Logika RAID:
- **RAID 0:** Każda awaria dysku powoduje awarię systemu.
- **RAID 1:** System jest odporny na awarię jednego dysku.
- **RAID 5:** System jest odporny na awarię jednego dysku.
- **RAID 6:** System jest odporny na awarię dwóch dysków.
4. **Koszty i Czasy Napraw:** Uwzględnia koszty utrzymania oraz czas potrzebny na przywrócenie systemu. 


## 📝 Licencja
## 🤝 Programiści
- **Oleksandr Radionenko**
- **Bohdan Stepanenko**
- **Mykhailo Dek**
