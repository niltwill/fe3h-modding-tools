import subprocess
import wave
import os
import argparse

def get_sample_count(wav_path):
    with wave.open(wav_path, 'rb') as wav:
        return wav.getnframes() * wav.getnchannels()

def pad_to_multiple_of_8_ffmpeg(input_path, output_path=None):
    sample_count = get_sample_count(input_path)
    remainder = sample_count % 8

    if remainder == 0:
        print(f"[OK] '{input_path}' already aligned to 8 samples.")
        #if output_path and input_path != output_path:
            #os.makedirs(os.path.dirname(output_path), exist_ok=True)
            #subprocess.run(["ffmpeg", "-y", "-i", input_path, "-c:a", "pcm_s16le", "-metadata", "encoder=", output_path],
            #               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    # Compute samples to add
    samples_to_add = 8 - remainder
    with wave.open(input_path, 'rb') as wav:
        framerate = wav.getframerate()
        channels = wav.getnchannels()
        layout = "mono" if channels == 1 else "stereo"

    # Calculate duration of silence to add
    silence_seconds = samples_to_add / (framerate * channels)

    if output_path is None:
        output_path = input_path

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    temp_silence = "temp_silence.wav"
    silence_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r={framerate}:cl={layout}",
        "-t", f"{silence_seconds}",
        "-ac", str(channels),
        temp_silence
    ]
    subprocess.run(silence_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Concatenate original + silence
    concat_cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", temp_silence,
        "-filter_complex", "[0][1]concat=n=2:v=0:a=1",
        output_path
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    os.remove(temp_silence)
    print(f"[DONE] Padded and saved to '{output_path}'")

def process_input(input_path, output_path=None):
    if os.path.isfile(input_path):
        if input_path.lower().endswith(".wav"):
            if output_path and os.path.isdir(output_path):
                rel_path = os.path.relpath(input_path, start=os.path.dirname(input_path))
                full_output_path = os.path.join(output_path, rel_path)
            else:
                full_output_path = output_path
            pad_to_multiple_of_8_ffmpeg(input_path, full_output_path)
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.lower().endswith(".wav"):
                    full_input_path = os.path.join(root, file)
                    if output_path:
                        rel_path = os.path.relpath(full_input_path, start=input_path)
                        full_output_path = os.path.join(output_path, rel_path)
                    else:
                        full_output_path = None
                    pad_to_multiple_of_8_ffmpeg(full_input_path, full_output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pad WAV files so sample count is divisible by 8 using FFmpeg.")
    parser.add_argument("input", help="Path to input WAV file or folder")
    parser.add_argument("-o", "--output", help="Optional output file or folder")
    args = parser.parse_args()

    process_input(args.input, args.output)
