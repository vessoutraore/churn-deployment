Un **README.md complet** Description claire, structure du projet, étapes d’installation/déploiement, images (placeholders), et badges.

---

```markdown
# 🚀 Churn Deployment

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.20+-red?logo=streamlit)](https://streamlit.io/)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-623CE4?logo=terraform)](https://www.terraform.io/)

## 📖 Description
Ce projet met en place une **API FastAPI** et une **application Streamlit** pour l’analyse de churn (attrition client).  
L’infrastructure est gérée via **Terraform** et déployée sur **AWS EC2**.  

Objectifs :  
- Fournir une API backend performante pour exposer des modèles ou endpoints.  
- Offrir une interface utilisateur via Streamlit pour l’exploration des résultats.  
- Gérer l’infrastructure comme du code (Infrastructure-as-Code) pour plus de fiabilité.  

---

## 📂 Structure du projet
```

.
├── churn/
│   ├── api/            # API FastAPI
│   │   ├── app.py
│   │   └── requirements.txt
│   └── streamlit/      # App Streamlit
│       ├── app.py
│       └── requirements.txt
├── infra/              # Infrastructure (Terraform)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   └── user\_data.sh
├── README.md
└── .gitignore

````

---

## 🖼️ Aperçu
### FastAPI Docs
![FastAPI Screenshot](./docs/images/fastapi-docs.png)

### Streamlit Dashboard
![Streamlit Screenshot](./docs/images/streamlit-dashboard.png)

👉 *(Remplace `./docs/images/...` par le chemin de tes vraies captures)*

---

## ⚙️ Installation locale

### API (FastAPI)
```bash
cd churn/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
````

Accès : [http://localhost:8000](http://localhost:8000)
Docs : [http://localhost:8000/docs](http://localhost:8000/docs)

### Streamlit

```bash
cd churn/streamlit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

Accès : [http://localhost:8501](http://localhost:8501)

---

## ☁️ Déploiement sur AWS (Terraform)

Prérequis :

* Terraform installé (`terraform -v`)
* AWS CLI configuré (`aws configure`)

### Étapes

```bash
cd infra
terraform init
terraform validate
terraform plan
terraform apply -auto-approve
```

À la fin du déploiement :

* API : `http://<EC2-PUBLIC-IP>:8000`
* Streamlit : `http://<EC2-PUBLIC-IP>:8501`

---

## 🔒 Sécurité

* **Ne jamais** exposer directement l’EC2 en prod → privilégier un **ALB (Application Load Balancer)**.
* Gérer les **secrets** (API keys, DB credentials) via **AWS SSM Parameter Store** ou **Secrets Manager**.

---

## 📜 Licence

Ce projet est publié sous licence [MIT](./LICENSE).

---

## ✨ Auteur

👤 **Youssouf Vessou TRAORÉ**
Chef de Département Technique & Opérations @ DBA — Passionné par le Cloud, l’IA et l’EdTech.

```

---

👉 Tu n’auras plus qu’à :
1. Créer un dossier `docs/images/` dans ton projet.  
2. Mettre des **captures d’écran** de ton API (`http://127.0.0.1:8000/docs`) et de ton Streamlit (`http://127.0.0.1:8501`).  
3. Pousser le tout sur GitHub (`git add . && git commit -m "docs: add README and screenshots" && git push`).  

---

Veux-tu que je t’ajoute aussi une **section “CI/CD GitHub Actions”** dans ce README (lint + tests + terraform validate) pour que ton repo soit vraiment pro ?
```
