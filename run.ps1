# 재의 백작 실행 스크립트 (Windows PowerShell)
#   .\run.ps1            게임 서버 실행 → http://127.0.0.1:8765
#   .\run.ps1 setup      가상환경 + PyTorch(CUDA) + Laya 설치, 베이스 모델 다운로드
#   .\run.ps1 train      판정 모델 파인튜닝 (models/laya-vn 생성)
#   .\run.ps1 check      대본 문법 검사
#   .\run.ps1 voice-setup  음성 생성 환경: .venv-tts(Qwen3 VoiceDesign) + WSL Ubuntu(Higgs TTS 3)
#   .\run.ps1 voice      대사 음성 일괄 생성 (tools\gen_voices.py, 인자 그대로 전달)
param([string]$cmd = "play")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = ".\.venv\Scripts\python.exe"

switch ($cmd) {
  "setup" {
    if (-not (Test-Path $py)) { py -3.11 -m venv .venv }
    & $py -m pip install --upgrade pip
    & $py -m pip install torch --index-url https://download.pytorch.org/whl/cu130
    & $py -m pip install "laya[serve]" datasets
    & $py -c "from huggingface_hub import snapshot_download; snapshot_download('convaiinnovations/laya-multilingual', local_dir='models/laya-multilingual')"
  }
  "train" { & $py training\train.py --full @args }
  "voice-setup" {
    # 목소리 디자인(Qwen3 VoiceDesign): Windows .venv-tts
    $tp = ".\.venv-tts\Scripts\python.exe"
    if (-not (Test-Path $tp)) { py -3.11 -m venv .venv-tts }
    & $tp -m pip install --upgrade pip
    & $tp -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu130
    & $tp -m pip install -U qwen-tts soundfile jiwer librosa   # jiwer·librosa: tools\check_voices.py
    & $tp -c "from huggingface_hub import snapshot_download as d; d('Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign', local_dir='models/Qwen3-TTS-12Hz-1.7B-VoiceDesign')"
    # 대사 낭독(Higgs TTS 3): WSL Ubuntu (vLLM-Omni는 Linux 전용)
    wsl -d Ubuntu -u root -- apt-get install -y -qq ffmpeg build-essential git python3-dev
    $setup = wsl -d Ubuntu -- wslpath -a (Join-Path $PSScriptRoot "tools\higgs\setup_wsl.sh")
    wsl -d Ubuntu -- bash $setup
  }
  "voice" { & ".\.venv-tts\Scripts\python.exe" tools\gen_voices.py @args }
  "check" { & $py server\compile_story.py --check }
  default {
    Start-Process "http://127.0.0.1:8765"
    & $py server\app.py --port 8765
  }
}
