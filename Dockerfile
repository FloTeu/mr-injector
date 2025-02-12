FROM python:3.12-slim

WORKDIR /app

# Set the locale to ensure UTF-8 support
# ENV LC_ALL=C.UTF-8
# ENV LANG=C.UTF-8

# Define build arguments for the Azure OpenAI endpoint
ARG AZURE_OPENAI_ENDPOINT
ARG AZURE_OPENAI_API_KEY
# Define a build argument for the streamlit global password
ARG STREAMLIT_PASSWORD
# Define a build argument for using openai embedding model (otherwise all-MiniLM-L6-v2 is used)
ARG USE_OPEN_AI_EMBEDDINGS
# Define a build argument for optional files
ARG FILES_URL=""
# Set the environment variable in the container
ENV AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT
ENV AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
ENV USE_OPEN_AI_EMBEDDINGS=${USE_OPEN_AI_EMBEDDINGS:-true}

# Install necessary packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    locales \
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

# Download files
RUN if [ -n "$FILES_URL" ]; then \
    curl -fsSL "$FILES_URL" -o /tmp/files.tar.gz && \
    tar -xzf /tmp/files.tar.gz --strip-components=1 -C /app/files/ && \
    rm /tmp/files.tar.gz; \
fi

# Create the secrets.toml file with the password only if it's provided
RUN mkdir /app/.streamlit
RUN bash -c 'if [ -n "$STREAMLIT_PASSWORD" ]; then \
        echo "password = \"$STREAMLIT_PASSWORD\"" > /app/.streamlit/secrets.toml; \
    fi'


# Setup virtual environment
RUN uv venv
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN uv sync --frozen

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["uv", "run", "streamlit", "run", "mr_injector/frontend/main.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]