# 재의 백작 — Laya 판정 API (Hugging Face Space, CPU)
FROM python:3.11-slim

RUN useradd -m -u 1000 user
WORKDIR /app
ENV HF_HOME=/tmp/hf PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# 모델은 빌드할 때 받아 둔다 (재시작 시 다운로드 없음)
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('ringwring/laya-vn', local_dir='models/laya-vn')"

COPY server/ server/
COPY story/ story/
RUN chown -R user /app
USER user

ENV LAYA_LOG=0 CORS_ORIGINS=https://ring-experimental.github.io
EXPOSE 7860
CMD ["python", "server/app.py", "--api-only", "--host", "0.0.0.0", "--port", "7860", "--device", "cpu"]
