import time
import random
import json
from datetime import datetime

print("="*50)
print("🚀 Capteur IoT Virtuel - balenaCloud Demo")
print("="*50)

compteur = 0

while True:
    # Générer des données aléatoires
    temperature = round(20 + random.uniform(-5, 10), 2)
    humidite = round(50 + random.uniform(-20, 30), 2)
    
    data = {
        "compteur": compteur,
        "timestamp": datetime.now().isoformat(),
        "temperature": temperature,
        "humidite": humidite,
        "alerte": temperature > 28
    }
    
    # Afficher
    symbole = "🚨" if data["alerte"] else "📊"
    print(f"{symbole} #{compteur:04d} | Temp: {temperature}°C | Hum: {humidite}%")
    
    if data["alerte"]:
        print("     ⚠️  ALERTE TEMPÉRATURE ÉLEVÉE!")
    
    compteur += 1
    time.sleep(5)  # Attendre 5 secondes