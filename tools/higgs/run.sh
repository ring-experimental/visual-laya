#!/usr/bin/env bash
# WSL에서 Higgs 대사 생성 실행 (tools/gen_voices.py lines가 호출). 로그: ~/tts/logs/voice_higgs.log
cd "$(dirname "$0")"
mkdir -p ~/tts/logs
~/tts/higgs/bin/python voice_higgs.py > ~/tts/logs/voice_higgs.log 2>&1
rc=$?
grep -a "^\[higgs\]\|Error\|Traceback" ~/tts/logs/voice_higgs.log | tail -20
exit $rc
