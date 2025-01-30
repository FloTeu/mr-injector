FROM python:3.12-slim

WORKDIR /app

# Define build arguments for the Azure OpenAI endpoint
ARG AZURE_OPENAI_ENDPOINT
ARG AZURE_OPENAI_API_KEY
# Define a build argument for the streamlit global password
ARG STREAMLIT_PASSWORD
# Set the environment variable in the container
ENV AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT
ENV AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

COPY mr_injector/ /app/mr_injector/
COPY files/ /app/files/
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
COPY README.md /app/README.md

# Create the secrets.toml file with the password only if it's provided
RUN mkdir /app/.streamlit
RUN bash -c 'if [ -n "$STREAMLIT_PASSWORD" ]; then \
        echo "password = \"$STREAMLIT_PASSWORD\"" > /app/.streamlit/secrets.toml; \
    fi'


# Setup virtual environment
RUN uv venv
RUN pip install --no-cache-dir torch==2.5.1 -f https://download.pytorch.org/whl/torch_stable.html
RUN uv sync --frozen

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["uv", "run", "streamlit", "run", "mr_injector/frontend/main.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]