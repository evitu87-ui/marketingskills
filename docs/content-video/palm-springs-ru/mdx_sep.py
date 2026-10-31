"""Minimal MDX-Net (UVR Inst HQ 3) instrumental separation with onnxruntime + numpy.
Usage: python3 mdx_sep.py model.onnx in.wav out_instrumental.wav
"""
import sys
import numpy as np
import soundfile as sf
import onnxruntime as ort

N_FFT, HOP, DIM_F, DIM_T = 6144, 1024, 3072, 256
N_BINS = N_FFT // 2 + 1
CHUNK = HOP * (DIM_T - 1)
TRIM = N_FFT // 2
GEN = CHUNK - 2 * TRIM
WIN = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(N_FFT) / N_FFT)).astype(np.float32)  # periodic hann


def stft(x):  # x: (C, CHUNK) -> (C, N_BINS, DIM_T) complex, center=True reflect pad
    pad = N_FFT // 2
    xp = np.pad(x, ((0, 0), (pad, pad)), mode='reflect')
    frames = np.stack([xp[:, i * HOP:i * HOP + N_FFT] for i in range(DIM_T)], axis=-1)  # (C, N_FFT, T)
    return np.fft.rfft(frames * WIN[None, :, None], axis=1)


def istft(S):  # S: (C, N_BINS, T) -> (C, CHUNK)
    frames = np.fft.irfft(S, n=N_FFT, axis=1) * WIN[None, :, None]
    C = S.shape[0]
    total = N_FFT + HOP * (DIM_T - 1)
    y = np.zeros((C, total), np.float32)
    wsum = np.zeros(total, np.float32)
    for i in range(DIM_T):
        y[:, i * HOP:i * HOP + N_FFT] += frames[:, :, i]
        wsum[i * HOP:i * HOP + N_FFT] += WIN ** 2
    wsum[wsum < 1e-8] = 1e-8
    y /= wsum
    pad = N_FFT // 2
    return y[:, pad:pad + CHUNK]


def main(model, inp, out):
    mix, sr = sf.read(inp, dtype='float32', always_2d=True)
    assert sr == 44100, sr
    mix = mix.T  # (2, N)
    if mix.shape[0] == 1:
        mix = np.repeat(mix, 2, 0)
    n = mix.shape[1]
    pad = GEN - n % GEN
    mixp = np.concatenate([np.zeros((2, TRIM), np.float32), mix, np.zeros((2, pad + TRIM), np.float32)], 1)
    sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
    iname = sess.get_inputs()[0].name
    outs = []
    i = 0
    while i < n + pad:
        w = mixp[:, i:i + CHUNK]
        S = stft(w)[:, :DIM_F, :]  # (2, F, T)
        x = np.stack([S[0].real, S[0].imag, S[1].real, S[1].imag])[None].astype(np.float32)
        y = sess.run(None, {iname: x})[0][0]  # (4, F, T)
        Sy = np.zeros((2, N_BINS, DIM_T), np.complex64)
        Sy[0, :DIM_F] = y[0] + 1j * y[1]
        Sy[1, :DIM_F] = y[2] + 1j * y[3]
        outs.append(istft(Sy)[:, TRIM:-TRIM])
        i += GEN
    inst = np.concatenate(outs, 1)[:, :n]
    sf.write(out, inst.T, sr)
    voc = mix - inst
    sf.write(out.replace('.wav', '_vocals.wav'), voc.T, sr)
    print('done', n / sr, 's')


if __name__ == '__main__':
    main(*sys.argv[1:4])
