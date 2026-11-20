import os
import wave
import struct
import numpy as np
import subprocess

SAMPLE_RATE = 24000

def generate_intro_chime(out_path: str, sample_rate: int = SAMPLE_RATE) -> str:
    """
    Generates a crisp, futuristic 3-tone electronic chord with exponential decay.
    Tones: D5 (587.3 Hz), A5 (880.0 Hz), D6 (1174.7 Hz) + soft high harmonic sparkle.
    """
    duration = 1.4
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Fundamental frequencies
    f1, f2, f3 = 587.33, 880.0, 1174.66
    
    # Envelopes
    decay1 = np.exp(-3.5 * t)
    decay2 = np.exp(-4.2 * t)
    decay3 = np.exp(-5.0 * t)
    
    # Synthesis
    signal = (
        0.35 * np.sin(2 * np.pi * f1 * t) * decay1 +
        0.30 * np.sin(2 * np.pi * f2 * t) * decay2 +
        0.25 * np.sin(2 * np.pi * f3 * t) * decay3 +
        0.10 * np.sin(2 * np.pi * 1760.0 * t) * np.exp(-7.0 * t) # Sparkle overtone
    )
    
    # Soft attack curve (first 15ms)
    attack_samples = int(sample_rate * 0.015)
    attack_ramp = np.linspace(0, 1, attack_samples)
    signal[:attack_samples] *= attack_ramp
    
    # Normalize to -3dB
    signal = signal / (np.max(np.abs(signal)) + 1e-6) * 0.7
    
    int_samples = (signal * 32767).astype(np.int16)
    with wave.open(out_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())
    return out_path

def generate_transition_whoosh(out_path: str, sample_rate: int = SAMPLE_RATE) -> str:
    """
    Generates a sleek cyber UI transition sweep (whoosh + soft digital blip).
    Duration: 0.55s
    """
    duration = 0.55
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Exponential frequency sweep from 250Hz up to 1600Hz and down
    freq = 300 + 1300 * np.sin(np.pi * t / duration)
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    
    # Bell-shaped envelope
    env = np.sin(np.pi * t / duration) ** 2
    
    # Add subtle filtered noise texture
    noise = np.random.uniform(-0.15, 0.15, len(t)) * env
    
    signal = 0.35 * np.sin(phase) * env + noise
    # Normalize to -4dB
    signal = signal / (np.max(np.abs(signal)) + 1e-6) * 0.6
    
    int_samples = (signal * 32767).astype(np.int16)
    with wave.open(out_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())
    return out_path

def generate_ambient_tech_bed(duration: float, out_path: str, sample_rate: int = SAMPLE_RATE) -> str:
    """
    Generates a very subtle, warm harmonic ambient drone (A2 110Hz + E3 164.8Hz)
    with a gentle 0.2Hz low-frequency oscillation. Plays softly in background (-26dB).
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Warm low drone chords
    f_root = 110.0   # A2
    f_fifth = 164.81 # E3
    f_sub = 55.0     # A1
    
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * t)
    
    signal = (
        0.4 * np.sin(2 * np.pi * f_root * t) +
        0.3 * np.sin(2 * np.pi * f_fifth * t) +
        0.3 * np.sin(2 * np.pi * f_sub * t)
    ) * lfo
    
    # Fade in / fade out
    fade_len = int(sample_rate * 1.5)
    if len(signal) > 2 * fade_len:
        signal[:fade_len] *= np.linspace(0, 1, fade_len)
        signal[-fade_len:] *= np.linspace(1, 0, fade_len)
        
    # Keep volume very soft (~0.05 amplitude = -26dB) so it ducks under the vocal track
    signal = signal / (np.max(np.abs(signal)) + 1e-6) * 0.06
    
    int_samples = (signal * 32767).astype(np.int16)
    with wave.open(out_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())
    return out_path

def build_mastered_broadcast_audio(speech_wav: str, total_duration: float, scene_durations: list, out_wav: str) -> str:
    """
    Uses FFmpeg to master speech with intro chime, transition whooshes at scene boundaries,
    and a ducked ambient tech pad in the background.
    """
    temp_dir = os.path.dirname(out_wav)
    chime_wav = os.path.join(temp_dir, "sfx_intro_chime.wav")
    whoosh_wav = os.path.join(temp_dir, "sfx_transition.wav")
    bed_wav = os.path.join(temp_dir, "sfx_ambient_bed.wav")
    
    generate_intro_chime(chime_wav)
    generate_transition_whoosh(whoosh_wav)
    generate_ambient_tech_bed(total_duration, bed_wav)
    
    # Calculate transition timestamps
    # Scene 1 -> 2, Scene 2 -> 3
    transitions = []
    accum = 0.0
    for d in scene_durations[:-1]:
        accum += d
        transitions.append(accum)
        
    # Construct FFmpeg complex filter to overlay SFX
    # Inputs:
    # 0: speech
    # 1: bed
    # 2: chime (at t=0)
    # 3+: whooshes (at t=transitions)
    cmd = ["ffmpeg", "-y", "-i", speech_wav, "-i", bed_wav, "-i", chime_wav]
    
    filter_parts = []
    # Mix bed with voice
    # Voice gets subtle broadcast mastering: highpass=70, acompressor, equalizer
    filter_parts.append("[0:a]highpass=f=75,acompressor=threshold=-20dB:ratio=2.8:attack=15:release=120,volume=1.1[voice_master]")
    filter_parts.append("[1:a]volume=0.85[bed_master]")
    filter_parts.append("[2:a]adelay=100|100,volume=0.45[chime_master]")
    
    mix_inputs = ["[voice_master]", "[bed_master]", "[chime_master]"]
    
    # Add whooshes at scene transitions
    input_idx = 3
    for t_sec in transitions:
        cmd.extend(["-i", whoosh_wav])
        delay_ms = int(t_sec * 1000)
        filter_parts.append(f"[{input_idx}:a]adelay={delay_ms}|{delay_ms},volume=0.5[whoosh_{input_idx}]")
        mix_inputs.append(f"[whoosh_{input_idx}]")
        input_idx += 1
        
    filter_parts.append(f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=longest:dropout_transition=2[outa]")
    
    cmd.extend([
        "-filter_complex", ";".join(filter_parts),
        "-map", "[outa]",
        "-ac", "2",
        "-ar", "24000",
        out_wav
    ])
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return out_wav
    except Exception as e:
        print(f"[AudioEffects] Warning mixing SFX, falling back to raw speech: {e}")
        return speech_wav
