
import json
from pathlib import Path

config_path = Path(__file__).resolve().parent / "config.json"

with config_path.open("r", encoding="utf-8") as file:
    config = json.load(file)

thresholds = config["thresholds"]

for metric, threshold in thresholds.items():
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        raise ValueError(f"Soglia non valida: {metric}")

    if not 0 <= threshold <= 100:
        raise ValueError(f"La soglia di {metric} deve essere tra 0 e 100")

print("Configurazione caricata correttamente.")
print(f"CPU: {thresholds['cpu_percent']}%")
print(f"RAM: {thresholds['memory_percent']}%")
print(f"Disco: {thresholds['disk_percent']}%")
