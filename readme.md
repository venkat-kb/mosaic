# MOSAIC: Grievance Redressal System

## Problem Statement: AI-Powered Citizen Grievance Redressal System

_Empowering communities through efficient grievance management._

![last-commit](https://img.shields.io/github/last-commit/venkat-kb/mosaic?style=flat&logo=git&logoColor=white&color=0080ff)
![repo-top-language](https://img.shields.io/github/languages/top/venkat-kb/mosaic?style=flat&color=0080ff)
![repo-language-count](https://img.shields.io/github/languages/count/venkat-kb/mosaic?style=flat&color=0080ff)

_Built with the tools and technologies:_

![Wasabi](https://img.shields.io/badge/Wasabi-01CD3E.svg?style=flat&logo=Wasabi&logoColor=white)
![spaCy](https://img.shields.io/badge/spaCy-09A3D5.svg?style=flat&logo=spaCy&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243.svg?style=flat&logo=NumPy&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=Python&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2.svg?style=flat&logo=Google-Gemini&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063.svg?style=flat&logo=Pydantic&logoColor=white)
![PyAudio](https://img.shields.io/badge/PyAudio-FF6B6B.svg?style=flat&logo=python&logoColor=white)
![SciKitLearn](https://img.shields.io/badge/Scikit--Learn-F7931E.svg?style=flat&logo=scikit-learn&logoColor=white)
![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-FFD21E.svg?style=flat&logoColor=black)
![WatsonX AI](https://img.shields.io/badge/WatsonX%20AI-052FAD.svg?style=flat&logo=IBM&logoColor=white)

---

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)

---

## Overview

Mosaic is a powerful grievance management tool designed to streamline community issue tracking and resolution, leveraging advanced technologies for optimal performance.

### Why Mosaic?

This project aims to enhance the efficiency of grievance handling while improving user experience. The core features include:

- **🔧 Dependency Management:** Ensures a consistent development environment with specified library versions.
- **📊 Grievance Management Models:** Organizes caller information and case details for efficient tracking.
- **🖥️ User-Friendly GUI:** Provides an intuitive interface for viewing and managing grievances.
- **🧠 Natural Language Processing:** Analyzes case descriptions for categorization and prioritization.
- **🚫 Spam Filtering:** Identifies and manages spam submissions effectively.
- **📈 Dynamic Data Integration:** Utilizes JSON files for real-time updates and categorization.
- **‼️ Prioritization:** Dynamically prioritizes the cases based on urgency, relevance and semantic weights of the concerned departments.

### Formula:

score = α \* Wi + (1 - α)(category accuracy) + thread_length

Where:

- **α** - Reinforcement learning coefficient.
- **Wi** - Semantic weight.
- **category accuracy** - Relevance w.r.t the department.
- **thread_length** - Urgency(number of calls received for the particular case from different callers).

---

## Getting Started

### Prerequisites

This project requires the following dependencies:

- **Programming Language:** Python
- **Package Manager:** Pip

### Installation

Build Mosaic from the source and install dependencies:

1. **Clone the repository:**

```sh
❯ git clone https://github.com/venkat-kb/mosaic
```

2. **Install all the requirements:**

```sh
❯ pip install -r requirements.txt

❯ python -m spacy download en_core_web_lg
```

3. **Make a .env file and put GEMINI_API_KEY inside it**

4. **Run the file:**

```sh
❯ python main.py
```

---

# Demo Video
