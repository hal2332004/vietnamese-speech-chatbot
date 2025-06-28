from huggingface_hub import snapshot_download

snapshot_download(repo_id="anhnh2002/vnTTS",
                  repo_type="model",
                  local_dir="model/")