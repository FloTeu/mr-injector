# Mr. Injector
<div style="text-align: center;">
    <img src="files/logo_mr_injector.png" alt="Demo Image" width="300"/>
</div>

## Overview

This project serves as a **demonstration of prompt injection** techniques aimed at educating users on how to identify and exploit vulnerabilities in systems that utilize **Large Language Models (LLMs)**. The demo is designed to be user-friendly and can be run locally, making it ideal for presentations and educational purposes.



## Features

- **Interactive Demo**: Explore various prompt injection techniques through an intuitive interface.
- **Local Setup**: Easily set up and run the demo on your local machine.
- **Educational Resource**: Learn about the implications of prompt injection in LLM systems.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.12 or higher
- uv installed

## Installation

To set up the project locally, follow these steps:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/FloTeu/mr-injector.git
   cd mr-injector
   # creates virtual environment
   uv sync
   
## Run locally

1. **Activate virtual environment**
   ```bash
   # execute this in root of the project
   . .venv/bin/activate
   ```
2. **Run streamlit frontend**
   ```bash
   # execute this in root of the project
   streamlit run mr_injector/frontend/main.py
   ```
 

   
