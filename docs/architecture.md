# 🏗️ Architecture de la Simulation balenaCloud IoT

## Vue d'ensemble

Ce document détaille l'architecture complète de la simulation balenaCloud, incluant les flux de données, les protocoles de communication, et les interactions entre composants.

---

## Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ENVIRONNEMENT LOCAL (Docker)                     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                         RÉSEAU DOCKER (iot-network)                 │ │
│  │                                                                      │ │
│  │  ┌──────────────────┐        ┌────────────────────┐               │ │
│  │  │   CAPTEUR EDGE   │        │   MQTT BROKER      │               │ │
│  │  │   (Container 1)  │◀──────▶│   (Container 2)    │               │ │
│  │  │                  │  MQTT  │                    │               │ │
│  │  │  • Python 3.11   │        │  • Mosquitto 2.0   │               │ │
│  │  │  • paho-mqtt     │        │  • Port 1883 (MQTT)│               │ │
│  │  │  • Génération    │        │  • Port 9001 (WS)  │               │ │
│  │  │    données IoT   │        │  • Anonymous auth  │               │ │
│  │  └──────────────────┘        └────────────────────┘               │ │
│  │         │                              │                           │ │
│  │         │                              │                           │ │
│  │         │ MQTT Topics:                 │                           │ │
│  │         │ • devices/{id}/data         │                           │ │
│  │         │ • devices/{id}/commands     │                           │ │
│  │         │                              │                           │ │
│  │         │                              │                           │ │
│  │         └──────────────────────────────┼───────────────────────────┘ │
│  │                                        │                             │
│  │                                        ▼                             │
│  │                             ┌────────────────────┐                  │
│  │                             │   DASHBOARD WEB    │                  │
│  │                             │   (Container 3)    │                  │
│  │                             │                    │                  │
│  │                             │  • Flask (Python)  │                  │
│  │                             │  • Chart.js        │                  │
│  │                             │  • MQTT Client     │                  │
│  │                             │  • REST API        │                  │
│  │                             │  • Port 80         │                  │
│  │                             └────────────────────┘                  │
│  │                                        │                             │
│  └────────────────────────────────────────┼─────────────────────────────┘
│                                           │                              │
└───────────────────────────────────────────┼──────────────────────────────┘
                                            │
                                            │ HTTP
                                            │ Port 8080 (mappé)
                                            │
                                            ▼
                                  ┌──────────────────┐
                                  │  NAVIGATEUR WEB  │
                                  │  (Hôte local)    │
                                  │                  │
                                  │  localhost:8080  │
                                  └──────────────────┘
```

---

## Flux de Données Détaillé

### 1. Publication de Données (Device → Cloud)

```
Capteur Edge                MQTT Broker              Dashboard Web
     │                            │                         │
     │  1. Génération données     │                         │
     │     (temp, hum, pression)  │                         │
     │                            │                         │
     │  2. PUBLISH                │                         │
     │  Topic: devices/001/data   │                         │
     │  QoS: 1                    │                         │
     │──────────────────────────▶ │                         │
     │                            │                         │
     │  3. PUBACK                 │                         │
     │◀────────────────────────── │                         │
     │                            │                         │
     │                            │  4. Message reçu        │
     │                            │  (souscription active)  │
     │                            │─────────────────────────▶
     │                            │                         │
     │                            │  5. Stockage mémoire    │
     │                            │     + Mise à jour UI    │
     │                            │                         │
```

**Format du message (JSON)** :
```json
{
  "device_id": "simulator-001",
  "timestamp": "2024-12-14T15:30:45.123456",
  "temperature": 23.45,
  "humidite": 62.3,
  "pression": 1013.2,
  "batterie": 98.5,
  "mode": "auto",
  "firmware": "v1.0.0",
  "alerte": false,
  "uptime": 1234567
}
```

---

### 2. Commandes Descendantes (Cloud → Device)

```
Navigateur                 Dashboard Web            MQTT Broker           Capteur Edge
     │                            │                       │                     │
     │  1. Utilisateur change     │                       │                     │
     │     paramètres (UI)        │                       │                     │
     │─────────────────────────▶  │                       │                     │
     │                            │                       │                     │
     │  2. POST /api/command      │                       │                     │
     │     {intervalle: 2}        │                       │                     │
     │─────────────────────────▶  │                       │                     │
     │                            │                       │                     │
     │                            │  3. PUBLISH           │                     │
     │                            │  Topic: devices/001/  │                     │
     │                            │         commands      │                     │
     │                            │  QoS: 1               │                     │
     │                            │──────────────────────▶│                     │
     │                            │                       │                     │
     │                            │                       │  4. Message reçu    │
     │                            │                       │  (callback)         │
     │                            │                       │─────────────────────▶
     │                            │                       │                     │
     │                            │                       │  5. Application     │
     │                            │                       │     de la config    │
     │                            │                       │                     │
     │  6. Réponse JSON           │                       │                     │
     │◀─────────────────────────  │                       │                     │
     │     {status: "success"}    │                       │                     │
```

**Types de commandes supportées** :
```json
{
  "device_id": "simulator-001",
  "mode": "auto|manuel|economie",
  "intervalle": 1-60,
  "seuil_alerte": 15.0-45.0,
  "actif": true|false,
  "update_firmware": "v1.1.0"
}
```

---

## Architecture des Services Docker

### Service 1 : MQTT Broker (Mosquitto)

```
┌─────────────────────────────────────┐
│      MQTT Broker (Mosquitto)       │
├─────────────────────────────────────┤
│  Image: eclipse-mosquitto:2.0      │
│  Container: mqtt-broker            │
│                                     │
│  Ports exposés:                    │
│  • 1883 (MQTT natif)               │
│  • 9001 (MQTT over WebSocket)     │
│                                     │
│  Configuration:                     │
│  • Anonymous auth: enabled         │
│  • Persistence: enabled            │
│  • Max connections: illimitées     │
│  • Log level: all                  │
│                                     │
│  Volume monté:                     │
│  • ./mosquitto.conf → /mosquitto/  │
│    config/mosquitto.conf           │
└─────────────────────────────────────┘
```

**Fichier de configuration** (`mosquitto.conf`) :
```conf
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest stdout
log_type all
```

---

### Service 2 : Capteur Edge

```
┌──────────────────────────────────────┐
│       Capteur Edge (Python)         │
├──────────────────────────────────────┤
│  Image: python:3.11-slim            │
│  Container: capteur-edge            │
│                                      │
│  Dépendances:                       │
│  • paho-mqtt (client MQTT)          │
│  • standard lib (random, time)      │
│                                      │
│  Variables d'environnement:         │
│  • BALENA_DEVICE_UUID               │
│  • BALENA_APP_ID                    │
│  • MQTT_BROKER=mqtt-broker          │
│  • MQTT_PORT=1883                   │
│                                      │
│  Fonctionnalités:                   │
│  • Génération données réalistes     │
│    (cycle jour/nuit simulé)         │
│  • Publication MQTT QoS 1           │
│  • Réception commandes              │
│  • Simulation OTA updates           │
│  • Système d'alertes                │
│                                      │
│  Topics MQTT:                       │
│  • Publish: devices/{uuid}/data     │
│  • Subscribe: devices/{uuid}/       │
│               commands               │
└──────────────────────────────────────┘
```

**Algorithme de génération de données** :
```python
# Température avec variation sinusoïdale
heure = datetime.now().hour + minute/60
variation = 5 * sin((heure - 6) * π / 12)
temperature = 22 + variation + bruit_gaussien(0, 0.8)

# Humidité inversement corrélée
humidite = 65 - (temperature - 22) * 2 + bruit_gaussien(0, 3)
humidite = clamp(30, 95, humidite)

# Pression atmosphérique
pression = 1013 + bruit_gaussien(0, 3)

# Batterie décroissante
batterie = 100 - (time % 10000) / 100
```

---

### Service 3 : Dashboard Web

```
┌──────────────────────────────────────────┐
│        Dashboard Web (Flask)            │
├──────────────────────────────────────────┤
│  Image: python:3.11-slim                │
│  Container: dashboard-web               │
│                                          │
│  Dépendances:                           │
│  • Flask (serveur web)                  │
│  • paho-mqtt (client MQTT)              │
│                                          │
│  Ports exposés:                         │
│  • 80 (HTTP) → 8080 (hôte)             │
│                                          │
│  Fonctionnalités Backend:               │
│  • Serveur Flask sur port 80            │
│  • Client MQTT (souscription)           │
│  • Stockage en mémoire (deque)          │
│  • API REST endpoints:                  │
│    - GET /                              │
│    - GET /api/data                      │
│    - POST /api/command                  │
│                                          │
│  Fonctionnalités Frontend:              │
│  • Jauges temps réel (4 métriques)     │
│  • Graphiques Chart.js (historique)    │
│  • Panneau de contrôles                │
│  • Système d'alertes visuelles         │
│  • Interface OTA updates                │
│  • Auto-refresh toutes les 2s           │
└──────────────────────────────────────────┘
```

**Endpoints API REST** :

| Endpoint | Méthode | Description | Réponse |
|----------|---------|-------------|---------|
| `/` | GET | Page HTML principale | HTML |
| `/api/data` | GET | Dernières données + historique | JSON |
| `/api/command` | POST | Envoyer commande au device | JSON |

**Format réponse `/api/data`** :
```json
{
  "latest": {
    "simulator-001": {
      "device_id": "simulator-001",
      "temperature": 23.45,
      "humidite": 62.3,
      ...
    }
  },
  "history": [
    { "timestamp": "...", "temperature": 23.45, ... },
    ...
  ],
  "devices": ["simulator-001", "simulator-002"]
}
```

---

## Protocoles et Communications

### MQTT (Message Queuing Telemetry Transport)

**Caractéristiques** :
- **Version** : MQTT 3.1.1
- **QoS utilisé** : 1 (At least once delivery)
- **Retain** : Non utilisé
- **Clean session** : True
- **Keep alive** : 60 secondes

**Structure des topics** :
```
devices/
  └── {device_uuid}/
      ├── data          (publish par device, subscribe par dashboard)
      └── commands      (publish par dashboard, subscribe par device)
```

**Avantages MQTT pour IoT** :
- ✅ Léger (overhead minimal)
- ✅ Pub/Sub découplé
- ✅ QoS pour fiabilité
- ✅ Support connexions instables
- ✅ Bi-directionnel natif

---

### HTTP/REST

**Utilisé pour** :
- Communication navigateur ↔ dashboard
- Réponses synchrones
- Interface utilisateur

**Endpoints implémentés** :
```
GET  /                 → Interface HTML
GET  /api/data         → Récupération données JSON
POST /api/command      → Envoi commandes
```

---

## Sécurité

### Niveau actuel (Démo/Développement)

**MQTT Broker** :
- ⚠️ Authentification anonyme activée
- ⚠️ Pas de TLS/SSL
- ⚠️ Topics ouverts (pas d'ACL)

**Dashboard** :
- ⚠️ Pas d'authentification utilisateur
- ⚠️ HTTP non chiffré
- ⚠️ CORS ouvert

### Recommandations Production

**MQTT Broker** :
- ✅ Username/password authentication
- ✅ TLS 1.2+ obligatoire
- ✅ ACL par topic et par device
- ✅ Certificats X.509 pour devices

**Dashboard** :
- ✅ Authentification JWT
- ✅ HTTPS avec certificat valide
- ✅ CORS restreint
- ✅ Rate limiting API

**Exemple configuration Mosquitto sécurisée** :
```conf
listener 8883
protocol mqtt
cafile /certs/ca.crt
certfile /certs/server.crt
keyfile /certs/server.key
require_certificate true

allow_anonymous false
password_file /mosquitto/config/password.txt

acl_file /mosquitto/config/acl.conf
```

---

## Scalabilité et Performance

### Limites de la démo actuelle

| Métrique | Valeur actuelle | Limite théorique |
|----------|-----------------|------------------|
| Devices simultanés | 1-2 | ~100 |
| Messages/seconde | ~0.2 | ~1000 |
| Historique stocké | 100 points | RAM disponible |
| Clients dashboard | 1-5 | ~50 |

### Optimisations possibles

**Backend** :
- Base de données pour persistance (PostgreSQL, InfluxDB)
- Cache Redis pour données temps réel
- Load balancing avec NGINX
- Clustering MQTT (HiveMQ, EMQX)

**Frontend** :
- WebSocket pour push temps réel
- Service Worker pour offline
- Pagination de l'historique
- Compression des données

---

## Comparaison avec Architecture Réelle balenaCloud

### Architecture Démo (locale)

```
PC Local
  └── Docker
      ├── MQTT Broker (simulation cloud)
      ├── Capteur (simulation device)
      └── Dashboard (simulation cloud)
```

### Architecture Réelle balenaCloud

```
Device Physique (ex: Raspberry Pi)
  └── balenaOS
      ├── Supervisor (orchestration)
      └── Conteneurs applicatifs
          ├── Capteur (app métier)
          └── Connecteur cloud
              └── VPN balenaCloud
                  ↓
              balenaCloud (SaaS)
                  ├── Fleet Management
                  ├── OTA Updates
                  ├── Monitoring
                  └── API/Dashboard
                      ↓
                  Utilisateur final
```

### Différences clés

| Aspect | Démo locale | balenaCloud réel |
|--------|-------------|------------------|
| **OS** | Docker sur OS hôte | balenaOS (Linux minimal) |
| **Réseau** | Docker network local | VPN chiffré vers cloud |
| **Updates** | Manual rebuild | OTA atomique avec rollback |
| **Monitoring** | Logs Docker | Dashboard centralisé cloud |
| **Scaling** | 1 machine | Milliers d'appareils |
| **Offline** | Non applicable | Résilient avec sync différée |

---

## Diagramme de Séquence : Cycle Complet

```
Utilisateur    Dashboard    MQTT Broker    Capteur
    │              │              │            │
    │              │              │            │ (Démarrage)
    │              │              │            │
    │              │              │◀───────────┤ CONNECT
    │              │              │            │
    │              │              │────────────▶ CONNACK
    │              │              │            │
    │              │              │◀───────────┤ SUBSCRIBE
    │              │              │            │ devices/001/commands
    │              │◀─────────────┤            │
    │              │  CONNECT     │            │
    │              │──────────────▶            │
    │              │              │            │
    │              │  SUBSCRIBE   │            │
    │              │  devices/+/data           │
    │              │──────────────▶            │
    │              │              │            │
    │              │              │            │
    │              │              │            │──┐ Génération
    │              │              │            │  │ données
    │              │              │            │◀─┘
    │              │              │            │
    │              │              │◀───────────┤ PUBLISH
    │              │              │            │ devices/001/data
    │              │              │            │ {temp: 23.5, ...}
    │              │              │            │
    │              │◀─────────────┤            │
    │              │ Message data │            │
    │              │              │            │
    │              │──┐            │            │
    │              │  │ Stockage   │            │
    │              │  │ + Update   │            │
    │              │◀─┘            │            │
    │              │              │            │
    │◀─────────────┤              │            │
    │  HTTP GET    │              │            │
    │  /api/data   │              │            │
    │              │              │            │
    │──────────────▶              │            │
    │  JSON data   │              │            │
    │              │              │            │
    │  (UI Update) │              │            │
    │              │              │            │
    │──────────────▶              │            │
    │ POST /api/   │              │            │
    │ command      │              │            │
    │ {interval:2} │              │            │
    │              │              │            │
    │              │──────────────▶            │
    │              │ PUBLISH      │            │
    │              │ devices/001/ │            │
    │              │ commands     │            │
    │              │              │────────────▶
    │              │              │ Message cmd│
    │              │              │            │
    │              │              │            │──┐ Application
    │              │              │            │  │ config
    │              │              │            │◀─┘
    │              │              │            │
    │              │              │            │ (Intervalle = 2s)
    │              │              │            │
```

---

## Conclusion

Cette architecture démontre les principes clés de balenaCloud :
- **Conteneurisation** des applications IoT
- **Communication asynchrone** via MQTT
- **Gestion centralisée** via dashboard
- **Bidirectionnalité** des flux de données
- **Modularité** et isolation des services

L'approche par simulation permet de comprendre les concepts sans investir dans du matériel, tout en restant fidèle à l'architecture réelle d'un déploiement balenaCloud en production.