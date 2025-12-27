import argparse
import os
import pathlib
import sys

import numpy as np

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from meetjot.audio.capture import RecordingConfig, record_dual_wav, list_devices


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--samplerate", type=int, default=48000)
    parser.add_argument("--channels", type=int, default=1)
    parser.add_argument("--outdir", type=str, default=str(pathlib.Path.cwd() / "out_audio"))
    parser.add_argument("--prefix", type=str, default="test")
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--mic-name", type=str, default=None)
    parser.add_argument("--speaker-name", type=str, default=None)
    parser.add_argument("--system-loopback-name", type=str, default=None)
    args = parser.parse_args()

    if args.list_devices:
        devices = list_devices()
        for d in devices:
            print(d)
        return 0

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    cfg = RecordingConfig(
        samplerate=args.samplerate,
        channels=args.channels,
        seconds=args.seconds,
        blocksize=1024,
    )

    mic_path = outdir / f"{args.prefix}_mic.wav"
    sys_path = outdir / f"{args.prefix}_system.wav"
    mix_path = outdir / f"{args.prefix}_mix.wav"

    result = record_dual_wav(
        cfg=cfg,
        mic_wav_path=str(mic_path),
        system_wav_path=str(sys_path),
        mix_wav_path=str(mix_path),
        mic_name=args.mic_name,
        speaker_name=args.speaker_name,
        system_loopback_name=args.system_loopback_name,
    )

    print("Recorded")
    print(f"mic: {result['mic_wav']}")
    print(f"system: {result['system_wav']}")
    print(f"mix: {result['mix_wav']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
