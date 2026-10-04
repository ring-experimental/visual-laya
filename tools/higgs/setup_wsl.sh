#!/usr/bin/env bash
# (최초 1회) WSL Ubuntu에 Higgs TTS 3 실행 환경 구성: uv, vLLM-Omni venv(~/tts/higgs), 모델, 오디오 토크나이저.
# 시스템 패키지는 root로 먼저: wsl -d Ubuntu -u root -- apt-get install -y ffmpeg build-essential git python3-dev
set -e
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
mkdir -p ~/tts/models && cd ~/tts
[ -d higgs ] || uv venv -q higgs -p 3.12
uv pip install -q -p higgs vllm==0.30.0 --torch-backend=auto
uv pip install -q -p higgs vllm-omni==0.30.0 huggingface_hub hf_xet
higgs/bin/hf download bosonai/higgs-tts-3-4b --local-dir models/higgs-tts-3-4b
higgs/bin/hf download k2-fsa/OmniVoice --include "audio_tokenizer/*"   # 레퍼런스 인코더
higgs/bin/python -c "import torch,vllm_omni;print('ok',torch.cuda.is_available())"
