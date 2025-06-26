import os
os.environ["CUDA_VISIBLE_DEVICES"] =  "0" # Tell it which GPU to use (or ignore if you're CPU-bound and patient!)

from vinorm import TTSnorm # Gotta normalize that Vietnamese text first
from src.services.TTS.f5tts_wrapper import F5TTSWrapper # Our handy wrapper class
import warnings
warnings.filterwarnings("ignore") # Ignore some warnings from the library
from src.utils.time_logger import timeit

@timeit("Text-to-Speech")
def tts_generate(text_to_generate, output_path):
    """
    Generate speech using the F5TTSWrapper with a cloned voice.
    
    :param text_to_generate: The text to generate speech for.
    :param output_path: Where to save the generated audio.
    :param ref_audio_path: Path to the reference audio file.
    :param ref_text: Text matching the reference audio.
    :param eraX_ckpt_path: Path to the model checkpoint.
    :param vocab_file: Path to the vocabulary file.
    """
    # --- Config ---
    # Path to the model checkpoint you downloaded from *this* repo
    # MAKE SURE this path points to the actual .pth or .ckpt file!
    eraX_ckpt_path = "src/services/TTS/model_48000.safetensors" # <-- CHANGE THIS!

    # Path to the voice you want to clone
    ref_audio_path = "src/services/TTS/update_213000_ref.wav" # <-- CHANGE THIS!

    # Path to the vocab file from this repo
    vocab_file = "src/services/TTS/vocab.txt" # <-- CHANGE THIS!

    # Where to save the generated sound
    output_dir = "src/services/TTS" # <-- CHANGE THIS if you want

    # --- Texts ---
    # Text matching the reference audio (helps the model learn the voice). Please make sure it match with the referrence audio!
    ref_text = "Thậm chí không ăn thì cũng có cảm giác rất là cứng bụng, chủ yếu là cái phần rốn...trở lên. Em có cảm giác khó thở, và ngủ cũng không ngon, thường bị ợ hơi rất là nhiều"

    # The text you want the cloned voice to speak
    text_to_generate = text_to_generate

    # --- Let's Go! ---
    print("Initializing the TTS engine... (Might take a sec)")
    tts = F5TTSWrapper(
        vocoder_name="vocos", # Using Vocos vocoder
        ckpt_path=eraX_ckpt_path,
        vocab_file=vocab_file,
        use_ema=False, # ALWAYS False as we converted from .pt to safetensors and EMA (where there is or not) was in there
    )

    # Normalize the reference text (makes it easier for the model)
    ref_text_norm = TTSnorm(ref_text)

    # Prepare the output folder
    os.makedirs(output_dir, exist_ok=True)

    print("Processing the reference voice...")
    # Feed the model the reference voice ONCE
    # Provide ref_text for better quality, or set ref_text="" to use Whisper for auto-transcription (if installed)
    tts.preprocess_reference(
        ref_audio_path=ref_audio_path,
        ref_text=ref_text_norm,
        clip_short=True # Keeps reference audio to a manageable length (~12s)
    )
    print(f"Reference audio duration used: {tts.get_current_audio_length():.2f} seconds")

    # --- Generate New Speech ---
    print("Generating new speech with the cloned voice...")

    # Normalize the text we want to speak
    text_norm = TTSnorm(text_to_generate)

    # You can generate multiple sentences easily
    # Just add more normalized strings to this list
    sentences = [text_norm]

    for i, sentence in enumerate(sentences):
        output_path = os.path.join(output_dir, f"generated_speech_{i+1}.wav")

        # THE ACTUAL GENERATION HAPPENS HERE!
        tts.generate(
            text=sentence,
            output_path=output_path,
            nfe_step=32,               # Denoising steps. More = slower but potentially better? (Default: 32)
            cfg_strength=2.0,          # How strongly to stick to the reference voice style? (Default: 2.0)
            speed=1.0,                 # Make it talk faster or slower (Default: 1.0)
            cross_fade_duration=0.15,  # Smooths transitions if text is split into chunks (Default: 0.15)
        )
        print(f"Boom! Audio saved to: {output_path}")

print("\nAll done! Check your output folder.")