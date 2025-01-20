# Mr. Injector
<div style="text-align: center;">
    <img src="files/logo_mr_injector.png" alt="Demo Image" width="300"/>
</div>

## Overview

This project serves as a **demonstration of prompt injection** techniques aimed at educating users on how to identify and exploit vulnerabilities in systems that utilize **Large Language Models (LLMs)**. The demo is designed to be user-friendly and can be run locally or in a containerized environment, making it ideal for presentations and educational purposes.



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

1. **Setup environment file**
   ```bash
   cp .env.template .env
   # populate .env file with values
   ```
   If you run the app locally, set DEBUG to True.
2. **Activate virtual environment**
   ```bash
   # execute this in root of the project
   . .venv/bin/activate
   ```
3. **Run streamlit frontend**
   ```bash
   # execute this in root of the project
   streamlit run mr_injector/frontend/main.py
   ```
 
## Run with Docker
1. **Setup environment file**
   ```bash
   cp .env.template .env
   # populate .env file with values
   ```
2. **Setup secret file**
   Streamlit secret file adds a simple layer of security with a global password
   ```bash
   cp secrets.toml.template secrets.toml
   # populate secrets.toml file with values
   ```
3. **Build docker image**
   ```bash
   docker build -t mr-injector .
   # or with Azure open ai setup
   docker build --build-arg AZURE_OPENAI_ENDPOINT=<your-endpoint-url> -t mr-injector .
   ```
4. **Run docker container**
   ```bash
   docker run -p 8501:8501 mr-injector
   ```


   
