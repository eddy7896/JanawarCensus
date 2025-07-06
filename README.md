# Janawar Census - Bird Acoustic Census System

## 🐦 Problem Statement

Bird species across the **Wular**, **Hygam**, and **Hokersar** wetlands (designated **Ramsar sites**) in Jammu & Kashmir have shown a **drastic population decline**:

- **Wular Lake**: 1.2 lakh birds (2020) ➝ 707 birds (2021)
- **Hokersar Wetlands**: 4.8 lakh birds (2020) ➝ 65,000 birds (2021)
- **Hygam Wetlands**: Notable long-term decline in migratory bird inflow

**Root Causes**:
- Habitat destruction
- Human encroachment
- Pollution

These factors are severely impacting **breeding**, **nesting grounds**, and the overall **ecological balance**.

---

## 💡 Proposed Solution

The **Janawar Census** is an **AI-powered, acoustic-based bird monitoring system** that uses a distributed network of **solar-powered Raspberry Pi devices** to record, identify, and analyze bird calls in real-time.

### Features:

- 📡 **Non-intrusive**, real-time, acoustic monitoring
- 🕊️ Species identification using **BirdNET**
- 🔴 Alerts for endangered species
- 📊 Web dashboard for data visualization and trends
- 🧭 Geo-tagged acoustic data for conservation planning

---

## 🎯 Objectives

- Enable **non-invasive**, round-the-clock wildlife monitoring
- Generate **real-time data and alerts** through a centralized dashboard
- Detect **endangered or rare bird species**
- Aid **policy-makers and conservationists** in ecological restoration

---

## 🛠️ System Components

### 📦 Hardware

| S.No | Component                                | Quantity | Purpose                                          |
|------|------------------------------------------|----------|--------------------------------------------------|
| 1    | Raspberry Pi 4 Model B (4GB)             | 1        | Main processing unit                             |
| 2    | ReSpeaker USB Microphone Array           | 1        | Directional bird sound capture                   |
| 3    | SIM7600E-H 4G HAT for Raspberry Pi       | 1        | GSM-based cloud connectivity                     |
| 4    | NEO-6M GPS Module                        | 1        | Location tagging                                 |
| 5    | Portronics USB Extension Cable (1.5m)    | 1        | Microphone positioning away from Pi              |
| 6    | Xiaomi 4i 20000mAh Power Bank            | 1        | USB-based power supply                           |
| 7    | Zeromeco Solar Panel Charge Controller   | 1        | Manages solar charging                           |
| 8    | Solar Universe 150W Solar Panel          | 1        | Off-grid solar power supply                      |
| 9    | External 256GB SSD                       | 1        | Local audio/data storage                         |

---

## 🧩 Software Stack

- 🎙️ **Audio Recording**: `ffmpeg`, `arecord`
- 🐦 **Bird Species Identification**: [BirdNET Analyzer](https://birdnet.cornell.edu/) ([GitHub](https://github.com/birdnet-team/BirdNET-Analyzer))
- 🐍 **Data Processing Scripts**: Python
- 🌐 **Backend API**: FastAPI
- 💻 **Frontend Dashboard**: Next.js
- 🗄️ **Database**: PostgreSQL

---

## 🔄 System Workflow

1. **Recording**: Device records ambient bird sounds using microphone arrays.
2. **Processing**: Audio analyzed using BirdNET for species identification.
3. **Location Tagging**: GPS data attached to each acoustic event.
4. **Data Upload**: Processed results uploaded via GSM/4G to central server.
5. **Dashboard Visualization**: Real-time graphs, alerts, and trends are shown.
6. **Endangered Species Alert**: Sends notifications on rare species detection.

---

## 📌 References

1. Ramsar Sites Data - Wetlands of India
2. *Asian Waterbird Census in Jammu and Kashmir (2015–2021)* – Spatial attributes and trend analysis

---

## 📂 Repository Structure

```
janawar-census/
├── backend/                  # FastAPI backend application
│   ├── app/                  # Main application code
│   ├── birdnet/              # BirdNET integration and models
│   ├── migrations/           # Database migrations
│   └── requirements.txt      # Python dependencies
│
├── edge-device/              # Edge device implementation
│   ├── audio_capture/        # Audio recording functionality
│   ├── gps_tracking/         # GPS location services
│   └── upload_scripts/       # Data upload utilities
│
├── frontend-app/             # Next.js frontend application
│   ├── app/                  # App router pages and layouts
│   ├── components/           # Reusable UI components
│   ├── contexts/             # React contexts
│   ├── lib/                  # Utilities and services
│   └── public/               # Static assets
│
├── docs/                     # Project documentation
│   ├── api/                  # API documentation
│   ├── deployment/           # Deployment guides
│   └── hardware/             # Hardware specifications
│
├── scripts/                  # Development and setup scripts
│   ├── database/             # Database management scripts
│   └── setup/                # Environment setup scripts
│
├── .gitignore               # Git ignore rules
├── docker-compose.yml       # Docker configuration
└── README.md               # Project documentation
```
