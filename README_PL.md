# Symulator Utrzymania Systemu Kolejowego
## 🚂 Przegląd
Ten projekt to framework symulacyjny do analizy niezawodności i efektywności kosztowej różnych polityk utrzymania w systemie kolejowym. Oblicza kluczowe wskaźniki, takie jak dostępność, przestoje, koszty utrzymania i miary niezawodności (MTBF, MTTR) poprzez symulację procesu awarii i napraw przy użyciu rozkładu Weibulla. Po przeprowadzeniu symulacji, kod zapisuje wyniki do pliku CSV i generuje wizualne porównania między politykami.

## ✨ Funkcje
- **Symulacja Wielu Polityk Utrzymania:**
  - Konserwacja Zapobiegawcza
  - Konserwacja Reaktywna
  - Konserwacja Predykcyjna
- **Kompleksowe Wskaźniki Analizy:**
  - Dostępność Systemu
  - Średni Czas Między Awariami (MTBF)
  - Średni Czas Do Naprawy (MTTR)
  - Koszty Utrzymania
  - Wskaźniki awaryjności poszczególnych komponentów
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
```bash
pip install numpy matplotlib scipy
```

### Konfiguracja
Symulator wykorzystuje plik konfiguracyjny JSON (`maintenance_policies.json`) do zdefiniowania:
- Parametrów symulacji
- Celów SLA
- Specyfikacji polityk utrzymania
- Szczegółów dotyczących komponentów

Przykładowa struktura konfiguracji:
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

### Uruchamianie Symulatora
```bash
python simulation.py
```

## 📊 Wyniki
Symulator generuje:
1. **Plik CSV z Wynikami** (`reliability_simulation_results.csv`):
   - Szczegółowe wskaźniki dla każdej polityki utrzymania
   - Analizy statystyczne
   - Status zgodności z SLA
2. **Wizualizacja** (`maintenance_policy_comparison.png`):
   - Porównawcze wykresy słupkowe dla kluczowych wskaźników
   - Analiza dostępności systemu
   - Wykresy porównania kosztów

## 📈 Przykładowe Wyniki
Na podstawie wyników symulacji:
- **Konserwacja Predykcyjna** osiąga najwyższą dostępność (97,73%) przy minimalnych przestojach
- **Konserwacja Zapobiegawcza** utrzymuje dobrą dostępność (94,99%) przy umiarkowanych kosztach
- **Konserwacja Reaktywna** wykazuje wyższe koszty i niższą dostępność (85,00%)

## 🛠️ Szczegóły Techniczne
### Kluczowe Klasy
- `RailwaySystemSimulator`: Główny silnik symulacji
- `MaintenancePolicy`: Obsługa konfiguracji polityk
- `Component`: Menedżer specyfikacji na poziomie komponentów

### Metodologia Symulacji
1. Wykorzystuje rozkład Weibulla do realistycznego modelowania awarii
2. Implementuje symulację Monte Carlo dla niezawodności statystycznej
3. Uwzględnia awarie na poziomie komponentów i systemu
4. Uwzględnia koszty utrzymania i czasy napraw

## 📝 Licencja
## 🤝 Programiści
- **Oleksandr Radionenko**
- **Bohdan Stepanenko**
- **Mykhailo Dek**
