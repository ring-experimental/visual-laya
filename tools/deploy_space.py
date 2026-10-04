"""HF Space(판정 API) 배포: space/ + server/*.py + story/ 를 Space 저장소에 올린다.

  .venv\Scripts\python.exe tools\deploy_space.py            # ringwring/visual-laya-judge
  .venv\Scripts\python.exe tools\deploy_space.py <owner/name>

먼저 'hf auth login' (write 권한). Space는 올린 뒤 자동으로 다시 빌드된다.
"""

import shutil
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parent.parent
REPO = sys.argv[1] if len(sys.argv) > 1 else "ringwring/visual-laya-judge"


def main():
    api = HfApi()
    api.create_repo(REPO, repo_type="space", space_sdk="docker", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        shutil.copytree(ROOT / "space", out, dirs_exist_ok=True)
        (out / "server").mkdir()
        for f in (ROOT / "server").glob("*.py"):
            shutil.copy2(f, out / "server" / f.name)
        shutil.copytree(ROOT / "story", out / "story")
        api.upload_folder(repo_id=REPO, repo_type="space", folder_path=out,
                          commit_message="Deploy from visual-laya", delete_patterns=["server/*", "story/*"])
    print(f"https://huggingface.co/spaces/{REPO}")


if __name__ == "__main__":
    main()
