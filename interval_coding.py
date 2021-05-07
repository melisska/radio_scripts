#!/usr/bin/env python3

import time, socket
import numpy as np
import matplotlib.pyplot as p
from argparse import ArgumentParser, RawTextHelpFormatter
from os import makedirs
from os.path import join, basename
from numba import njit
from struct import pack, unpack
from sys import argv, stdout, exit
from math import radians
from scipy.io.wavfile import write, read


def plot_xlist(lst_y, lst_x=[], labels=[], colors=[], scatters=[], linestyles=[], title="", savepath="last_plot.png", show=0, xlabel="x", ylabel="y", chunk_size=0, shift=0, figsize=(12, 8), div_line=0, xticks=[], xticksfreq=1, projection=None, x_k=0, y_k=0, peak=0):
    fig = p.figure(1, figsize=figsize)
    #fig, ax = plt.subplots()
    axes = p.axes(projection=projection)

    if projection == "polar":
        axes.set_rmax(1)
        axes.set_rlabel_position(0)
        axes.grid(True)
        xlabel = ""
        ylabel = ""
        title += "\n"
    else:
        axes.ticklabel_format(style="plain")

    p.title(title)
    p.xlabel(xlabel)
    p.ylabel(ylabel)

    if lst_x == []:
        x = np.arange(lst_y[0].shape[0])
        if shift != 0:
            x = x + shift
        if chunk_size != 0:
            x = x * chunk_size
        for i in range(len(lst_y)):
            lst_x.append(x)
    if xticks:
        p.xticks(lst_x[0][::xticksfreq], xticks[::xticksfreq], rotation=45, fontsize=10)

    for i in range(len(lst_y)):
        if type(peak) == type(list()):
            if i in peak:
                axes_peaks(lst_y[i], axes, x=lst_x[i], x_k=x_k, y_k=y_k, chunk_size=chunk_size, shift=shift)
        elif peak:
            axes_peaks(lst_y[i], axes, x=lst_x[i], x_k=x_k, y_k=y_k, chunk_size=chunk_size, shift=shift)
        if labels == []:
            label = str(i)
        else:
            label = labels[i]
        if linestyles == []:
            linestyle = "-"
        else:
            linestyle = linestyles[i]
        if scatters == []:
            scatter = 0
        else:
            scatter = scatters[i]
        if div_line > 0:
            if type(lst_x[i]) == type(list()):
                lst_x_length = len(lst_x[i])
            else:
                lst_x_length = lst_x[i].shape[0]
            for j in range(lst_x_length):
                if lst_x[i][j] % div_line == 0:
                    p.axvline(x=lst_x[i][j], color='k', linestyle='--')
        if scatter > 0:
            if colors:
                p.scatter(lst_x[i], lst_y[i], s=scatter, label = label, linestyle=linestyle, color = colors[i])
            else:
                p.scatter(lst_x[i], lst_y[i], s=scatter, label = label, linestyle=linestyle)
        else:
            if colors:
                p.plot(lst_x[i], lst_y[i], label = label, linestyle=linestyle, color = colors[i])
            else:
                p.plot(lst_x[i], lst_y[i], label = label, linestyle=linestyle)

    p.legend()
    p.savefig(savepath)
    if show:
        p.show()
    p.close()

def interval_create(carrier_freq, pulse_freqs, samp_rate, count, times, flag=1, mode="float"):
    #print(samp_rate)
    pulse_freq = round(np.average(interval_freqs))

    #array = np.array([], dtype="float")

    size = 0

    for i in range(pulse_freqs.shape[0]):
        duration = count * round(samp_rate / carrier_freq)
        space = round(samp_rate / pulse_freqs[i]) - duration
        size += duration + space

    array = np.zeros(size, dtype="float")

    acc = 0

    for i in range(pulse_freqs.shape[0]):
        duration = count * round(samp_rate / carrier_freq)
        space = round(samp_rate / pulse_freqs[i]) - duration

        time = np.arange(0, duration/samp_rate, 1/samp_rate)

        pulse = np.abs((np.sin(2*np.pi*carrier_freq * time - np.pi/2) + 1) / 2)
        #print(pulse.shape[0])

        array[acc:acc+duration] = pulse
        acc += duration + space

    if mode == "int16":
        array = np.int16(32767 * array)

    total = array
    for i in range(times - 1):
        array = np.hstack((total, array))

    time = np.arange(0, array.shape[0]/samp_rate, 1/samp_rate)
    return array, time


def interval_coding(carrier_freq, interval_freqs, samp_rate, count=1, times=1, mode="int16", wav=0, show=0):
    interval_freqs = np.array(interval_freqs)
    pulse_freq = round(np.average(interval_freqs))

    array, time = interval_create(carrier_freq, interval_freqs, samp_rate, count, times, mode=mode)

    directory = "output"

    if wav:
        makedirs(directory, exist_ok=True)
        name = "pulse{:d}_count{:d}_carrier{:d}".format(pulse_freq, count, carrier_freq)
        wav_path = join(directory, name+".wav")
        write(wav_path, samp_rate, array)

    if show:
        makedirs(directory, exist_ok=True)
        title = "samp_rate={:d}\npulse_freq={:.2f}, carrier_freq={:.2f}".format(samp_rate, pulse_freq, carrier_freq)

        lst_y = [array]
        lst_x = [time]

        labels = ["pulse", "sine"]
        colors = ["green", "magenta"]
        linestyles = ["-", ":"]

        img_path_wave = join(directory, name+"_waveform.png")

        lst_y = [array[0:samp_rate]]   #[array]
        lst_x = [time[0:samp_rate]]    #[time]
        projection = None

        plot_xlist(lst_y, lst_x=lst_x, labels=labels, colors=colors, linestyles=linestyles, title=title, div_line=1, xticksfreq=1, xlabel="time (sec)", ylabel="amplitude", projection=projection, savepath=img_path_wave, show=show)
    return array



version = "0.0.1"


if __name__ == "__main__":
    banner = '''\033[1;m\033[10;32m
interval_coding                 
\033[1;m'''


    """
./interval_coding.py double.bin -f 501 -s 80000 -c 32 -t 1
./interval_coding.py double.bin -f 520 -s 80000 -c 20 -t 1
./interval_coding.py double.bin -f 2000 -s 80000 -c 20 -t 1
./interval_coding.py double.bin -f 3000 -s 80000 -c 20 -t 1
    """

    """
./interval_coding.py byte.bin -f 501 -s 80000 -c 4 -t 1 -r byte
    """

    usage = './interval_coding.py double.bin -f 501 -s 80000 -c 32 -t 1'

    parser = ArgumentParser(description=banner,
                            formatter_class=RawTextHelpFormatter,
                            epilog=usage)

    parser.add_argument('filepath', type=str, help="Binary Data Filepath")

    parser.add_argument("-s",'--sample_rate','--rate', dest='samp_rate', type=int, default=44000, help="Sample Rate")
    parser.add_argument("-f",'--carrier', dest='carrier_freq', type=int, default=2000, help="Carrier Frequency")

    parser.add_argument("-t",'--times', dest='times', type=int, default=1, help="Repeating times")
    parser.add_argument("-c",'--count', dest='count', type=int, default=1, help="Count")

    parser.add_argument("-r",'--read', dest='read', type=str, default='double', help="[double, float, byte]")
    parser.add_argument("-m",'--mode', dest='mode', type=str, default='int16', help="Mode [int16]")
    
    args = parser.parse_args()

    # help/exit section
    if len(argv) == 1:
        parser.print_help()
        exit(1)

    with open(args.filepath, "rb") as f:
        print("[*] data reading...")
        if args.read in ["double", "float"]:
            if args.read == "double":
                k = 8
                s = "d"
            elif args.read == "float":
                k = 4
                s = "f"
            data = f.read()
            interval_freqs = []
            for i in range(len(data) // k):
                chunk = data[i*k:(i+1)*k]
                interval_freqs.append(unpack(s, chunk)[0])
            print(interval_freqs)
        else:
            interval_freqs = list(bytearray(f.read()))
        print("[*] intervals = {:d}".format(len(interval_freqs)))
        print("[*] done!")

    print("[*] generating...")
    interval_coding(args.carrier_freq, interval_freqs, args.samp_rate, count=args.count, times=args.times, mode=args.mode, wav=1, show=1)
    print("[*] done!")



