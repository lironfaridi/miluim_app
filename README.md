# 🛡️ Tactical Resource Optimization & Platoon Management Engine

*Developed by Liron Faridi | Data Analyst*

## 🎯 The Challenge
During active reserve duty, managing the leave schedules of a combat company (comprising multiple specialized platoons) is a highly complex resource-allocation problem. Relying on static Excel sheets created critical blind spots, risking operational readiness by accidentally allowing too many essential personnel (e.g., Medics, APC Drivers, Commanders) to be off-base simultaneously.

## 💡 The Solution
I developed a full-stack, data-driven web application that transitions workforce management from manual spreadsheets to an automated constraint-satisfaction engine. The system actively monitors real-time staffing levels and automatically blocks leave requests that would violate the unit's minimum operational requirements.

## 🚀 Key Features
* **Dynamic Logic Engine:** Automatically prevents scheduling conflicts based on customizable minimum-role constraints.
* **Real-Time KPIs & Gantt Visualization:** Instant overview of active personnel, soldiers on leave, and overall readiness status using interactive Plotly charts.
* **Multi-Unit Scalability:** Independent database configurations for different operational platoons.

## 🛠️ Tech Stack
* **Frontend:** Streamlit, Plotly (Data Visualization)
* **Backend & Logic:** Python
* **Database & ORM:** SQLite, SQLAlchemy
* **Deployment:** Streamlit Community Cloud

---
[👉 Click here to view the live web app](https://miluimapp-dtomlbzsprazvfypctrjnm.streamlit.app/)
