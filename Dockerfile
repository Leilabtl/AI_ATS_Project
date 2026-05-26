# ── Stage 1: dependency builder ──────────────────────────────────────────────
# Install all Python packages into an isolated venv so Stage 2 can copy just
# the compiled dependencies without build tools (gcc, pip cache, etc.).
FROM python:3.11-slim AS builder

WORKDIR /build

RUN python -m venv /build/venv
ENV PATH="/build/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: lean runtime image ───────────────────────────────────────────────
# Copy only the venv and application code — no build toolchain in the final image.
FROM python:3.11-slim AS runtime

WORKDIR /app

# curl is needed for the HEALTHCHECK only
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY . .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
