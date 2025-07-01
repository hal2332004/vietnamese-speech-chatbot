# Usage
Clone repo
```bash
git clone https://github.com/nguyenhoanganh2002/XTTSv2-Finetuning-for-New-Languages.git
cd XTTSv2-Finetuning-for-New-Languages
pip install -r requirements.txt
```

Pull model's weights
```python
from huggingface_hub import snapshot_download

snapshot_download(repo_id="anhnh2002/vnTTS",
                  repo_type="model",
                  local_dir="model/")
```

Load model
```python
from pprint import pprint
import torch
import torchaudio
from tqdm import tqdm
from underthesea import sent_tokenize
from vinorm import TTSnorm
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

device = "cuda:0"

xtts_checkpoint = "model/model.pth"
xtts_config = "model/config.json"
xtts_vocab = "model/vocab.json"

config = XttsConfig()
config.load_json(xtts_config)
XTTS_MODEL = Xtts.init_from_config(config)
XTTS_MODEL.load_checkpoint(config,
                            checkpoint_path=xtts_checkpoint,
                            vocab_path=xtts_vocab,
                            use_deepspeed=False)
XTTS_MODEL.to(device)
```

Preprocessing and chunking
```python
def preprocess_text(text, language="vi"):
    if language == "vi":
        text = TTSnorm(text, unknown=False, lower=False, rule=True)
    
    # split text into sentences
    if language in ["ja", "zh-cn"]:
        sentences = text.split("。")
    else:
        sentences = sent_tokenize(text)

    chunks = []
    chunk_i = ""
    len_chunk_i = 0
    for sentence in sentences:
        chunk_i += " " + sentence
        len_chunk_i += len(sentence.split())
        if len_chunk_i > 30:
            chunks.append(chunk_i.strip())
            chunk_i = ""
            len_chunk_i = 0

    if (len(chunks) > 0) and (len_chunk_i < 15):
        chunks[-1] += chunk_i
    else:
        chunks.append(chunk_i)

    return chunks
```

Generate latent embeddings for the speaker
```python
speaker_audio_file = "model/vi_man.wav"

gpt_cond_latent, speaker_embedding = XTTS_MODEL.get_conditioning_latents(
    audio_path=speaker_audio_file,
    gpt_cond_len=XTTS_MODEL.config.gpt_cond_len,
    max_ref_length=XTTS_MODEL.config.max_ref_len,
    sound_norm_refs=XTTS_MODEL.config.sound_norm_refs,
)
```

Inference
```python
def tts(
    model: Xtts,
    text: str,
    language: str,
    gpt_cond_latent: torch.Tensor,
    speaker_embedding: torch.Tensor,
    verbose: bool = False,
):
    # preprocess text
    chunks = preprocess_text(text, language)

    wav_chunks = []
    for text in tqdm(chunks):
        if text.strip() == "":
            continue
        wav_chunk = model.inference(
            text=text,
            language=language,
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            length_penalty=1.0,
            repetition_penalty=10.0,
            top_k=10,
            top_p=0.5,
        )

        wav_chunk["wav"] = torch.tensor(wav_chunk["wav"])

        wav_chunks.append(wav_chunk["wav"])

    out_wav = torch.cat(wav_chunks, dim=0).unsqueeze(0).cpu()

    return out_wav

from IPython.display import Audio

audio = tts(
    model=XTTS_MODEL,
    text="Xin chào, tôi là một hệ thống chuyển đổi văn bản tiếng Việt thành giọng nói.", #Hello, I am a Vietnamese text to speech conversion system.
    language="vi",
    gpt_cond_latent=gpt_cond_latent,
    speaker_embedding=speaker_embedding,
    verbose=True,
)

Audio(audio, rate=24000)
```

# License
This project uses a model licensed under the Coqui Public Model License 1.0.0, which permits non-commercial use only. This includes personal research, testing, and charitable purposes. Commercial entities may use it for non-commercial research and evaluation. Revenue-generating activities are prohibited. Users must include the license terms when distributing the model or its outputs. For full details, please refer to: https://coqui.ai/cpml