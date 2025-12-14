🌐 balenaCloud IoT Simulation

Projet : Comparaison plateformes IoT 2024-2025

Simulation d'un système IoT Edge complet sans matériel physique.

⚡ Quick Start
bash# 1. Cloner
git clone https://github.com/Nourkes/iot_project.git
cd iot_project/balena-demo

# 2. Lancer
docker-compose up

# 3. Ouvrir
http://localhost:8080
Prérequis : Docker Desktop installé

🎯 Fonctionnalités
✅ Capteur virtuel (température, humidité, pression)
✅ Dashboard web temps réel avec graphiques
✅ Commandes bidirectionnelles (cloud ↔ device)
✅ Simulation OTA updates
✅ Système d'alertes automatiques

🏗️ Architecture
Capteur (Python) ──MQTT──▶ Broker (Mosquitto) ──▶ Dashboard (Flask)
                              ▲                         │
                              └─────── Commandes ───────┘
3 conteneurs Docker :

mqtt-broker : Communication pub/sub
capteur : Génération données IoT
dashboard : Visualisation & contrôle


🎮 Tests rapides
Test 1 : Changer l'intervalle

Dashboard → "Intervalle" = 2 secondes
Cliquer "Envoyer Configuration"
Terminal → Le capteur passe à 2s

Test 2 : Alerte température

"Seuil d'alerte" = 20°C
Envoyer configuration
Bannière rouge apparaît quand temp > 20°C

Test 3 : OTA Update

Sélectionner version v1.1.0
Cliquer "Déployer Mise à Jour"
Terminal → Firmware mis à jour


📁 Structure
balena-demo/
├── docker-compose.yml     # Orchestration
├── mosquitto.conf         # Config MQTT
├── capteur/               # Service capteur
├── dashboard/             # Service dashboard
└── scripts/               # Scripts utilitaires

🛠️ Commandes
bashdocker-compose up          # Démarrer
docker-compose logs -f     # Voir logs
docker-compose down        # Arrêter
docker-compose ps          # État services
