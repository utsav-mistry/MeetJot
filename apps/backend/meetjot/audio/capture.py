from __future__ import annotations

import dataclasses
import threading
import wave
from typing import Any

import numpy as np
import soundcard as sc


@dataclasses.dataclass(frozen=True)
class RecordingConfig:
    samplerate: int = 48000
    channels: int = 1
    seconds: float = 10.0
    blocksize: int = 1024


def _float_to_int16(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    x = np.clip(x, -1.0, 1.0)
    return (x * 32767.0).astype(np.int16)


def _write_wav_int16(path: str, data_int16: np.ndarray, samplerate: int, channels: int) -> None:
    data_int16 = np.asarray(data_int16, dtype=np.int16)
    if channels == 1 and data_int16.ndim == 2:
        data_int16 = data_int16[:, 0]
    if channels > 1 and data_int16.ndim == 1:
        data_int16 = np.repeat(data_int16[:, None], channels, axis=1)

    if data_int16.ndim == 1:
        frames = data_int16.tobytes()
    else:
        frames = data_int16.reshape(-1).tobytes()

    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(frames)


def list_devices() -> list[dict[str, Any]]:
    mics = sc.all_microphones(include_loopback=False)
    loopbacks = sc.all_microphones(include_loopback=True)
    speakers = sc.all_speakers()

    out: list[dict[str, Any]] = []
    for m in mics:
        out.append({"type": "microphone", "name": m.name})
    for s in speakers:
        out.append({"type": "speaker", "name": s.name})
    for lb in loopbacks:
        if lb.name not in {m.name for m in mics}:
            out.append({"type": "loopback_microphone", "name": lb.name})
    return out


def _resolve_loopback_microphone_for_speaker(speaker: sc.Speaker) -> sc.Microphone:
    """Resolve the system-audio capture device for a given speaker.

    On some platforms/versions, Speaker.loopback_microphone() is not available.
    In those cases, soundcard exposes loopback sources as Microphone devices when
    include_loopback=True.
    """

    loopbacks = sc.all_microphones(include_loopback=True)

    # Common case: loopback mic has the exact same name as the speaker.
    for lb in loopbacks:
        if lb.name == speaker.name:
            return lb

    # Fallback: partial match.
    speaker_name_l = speaker.name.lower()
    for lb in loopbacks:
        if speaker_name_l in lb.name.lower():
            return lb

    raise RuntimeError(
        "Could not find a loopback microphone for the selected speaker. "
        "Run record_test.py --list-devices and pass an explicit --system-loopback-name. "
        f"Selected speaker: {speaker.name}"
    )


def record_dual_wav(
    *,
    cfg: RecordingConfig,
    mic_wav_path: str,
    system_wav_path: str,
    mix_wav_path: str | None = None,
    mic_name: str | None = None,
    speaker_name: str | None = None,
    system_loopback_name: str | None = None,
) -> dict[str, str]:
    mic = sc.get_microphone(mic_name, include_loopback=False) if mic_name else sc.default_microphone()
    speaker = sc.get_speaker(speaker_name) if speaker_name else sc.default_speaker()
    if system_loopback_name:
        system_mic = sc.get_microphone(system_loopback_name, include_loopback=True)
    else:
        system_mic = _resolve_loopback_microphone_for_speaker(speaker)

    mic_chunks: list[np.ndarray] = []
    sys_chunks: list[np.ndarray] = []

    exc: list[BaseException] = []

    def rec_mic() -> None:
        try:
            with mic.recorder(samplerate=cfg.samplerate, channels=cfg.channels, blocksize=cfg.blocksize) as r:
                frames = int(cfg.seconds * cfg.samplerate)
                remaining = frames
                while remaining > 0:
                    n = min(cfg.blocksize, remaining)
                    chunk = r.record(numframes=n)
                    mic_chunks.append(chunk)
                    remaining -= n
        except BaseException as e:
            exc.append(e)

    def rec_sys() -> None:
        try:
            with system_mic.recorder(samplerate=cfg.samplerate, channels=cfg.channels, blocksize=cfg.blocksize) as r:
                frames = int(cfg.seconds * cfg.samplerate)
                remaining = frames
                while remaining > 0:
                    n = min(cfg.blocksize, remaining)
                    chunk = r.record(numframes=n)
                    sys_chunks.append(chunk)
                    remaining -= n
        except BaseException as e:
            exc.append(e)

    t1 = threading.Thread(target=rec_mic, daemon=True)
    t2 = threading.Thread(target=rec_sys, daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    if exc:
        raise exc[0]

    mic_audio = np.concatenate(mic_chunks, axis=0) if mic_chunks else np.zeros((0, cfg.channels), dtype=np.float32)
    sys_audio = np.concatenate(sys_chunks, axis=0) if sys_chunks else np.zeros((0, cfg.channels), dtype=np.float32)

    min_len = min(mic_audio.shape[0], sys_audio.shape[0])
    mic_audio = mic_audio[:min_len]
    sys_audio = sys_audio[:min_len]

    mic_i16 = _float_to_int16(mic_audio)
    sys_i16 = _float_to_int16(sys_audio)

    _write_wav_int16(mic_wav_path, mic_i16, cfg.samplerate, cfg.channels)
    _write_wav_int16(system_wav_path, sys_i16, cfg.samplerate, cfg.channels)

    result: dict[str, str] = {"mic_wav": mic_wav_path, "system_wav": system_wav_path}

    if mix_wav_path:
        mix = np.clip(mic_audio + sys_audio, -1.0, 1.0)
        mix_i16 = _float_to_int16(mix)
        _write_wav_int16(mix_wav_path, mix_i16, cfg.samplerate, cfg.channels)
        result["mix_wav"] = mix_wav_path

    return result
