# -*- coding: utf-8 -*-
import os
import sys
import vapoursynth as vs
import platform
import tempfile
import json

from multiprocessing import cpu_count

# workaround for relative imports with embedded python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from utils.vfi_inference import vfi_frame_merger

ossystem = platform.system()
core = vs.core

if ossystem == "Windows":
    tmp_dir = tempfile.gettempdir() + "\\enhancr\\"
else:
    tmp_dir = tempfile.gettempdir() + "/enhancr/"

# load json with input file path and framerate
with open(os.path.join(tmp), encoding='utf-8') as f:
    data = json.load(f)
    video_path = data['file']
    frame_rate = data['framerate']
    engine = data['engine']
    streams = data['streams']
    sceneDetection = data['sc']
    frameskip = data['skip']
    padding = data['padding']
    sensitivity = data['sensitivity']
    sensitivityValue = data['sensitivityValue']
    ToPadWidth = data['toPadWidth']
    ToPadHeight = data['toPadHeight']

core.num_threads = cpu_count()

cwd = os.getcwd()
vsmlrt_path = os.path.join(cwd, '..', 'env', 'Library', 'vstrt.dll')
core.std.LoadPlugin(path=vsmlrt_path)

clip = core.lsmas.LWLibavSource(source=f"{video_path}", cache=0)

if frameskip:
    offs1 = core.std.BlankClip(clip, length=1) + clip[:-1]
    offs1 = core.std.CopyFrameProps(offs1, clip)
    # use ssim for similarity calc
    clip = core.vmaf.Metric(clip, offs1, 2)

if sceneDetection:
    if sensitivity:
        clip = core.misc.SCDetect(clip=clip, threshold=sensitivityValue)
    else:
        clip = core.misc.SCDetect(clip=clip, threshold=0.180)

if padding:
    clip = core.std.AddBorders(clip, right=ToPadWidth, top=ToPadHeight)

clip = vs.core.resize.Bicubic(clip, format=vs.RGBS, matrix_in_s="709")

clip_pos1 = clip[1:]
clip_pos2 = clip.std.Trim(first=0,last=clip.num_frames-2)
clipstack =  [clip_pos1,clip_pos2]

output = core.trt.Model(
   clipstack,
   engine_path=engine,
   num_streams=int(streams)*4,
)
output=core.std.Interleave([clip,output])

clip1 = core.std.Interleave([clip, clip])

output = vfi_frame_merger(clip1, output)

if padding:
    output = core.std.Crop(clip, right=ToPadWidth, top=ToPadHeight)

output = vs.core.resize.Bicubic(output, format=vs.YUV422P8, matrix_s="709")

print("Starting video output | Threads: " + str(cpu_count()) + " | " + "Streams: " + streams, file=sys.stderr)
output.set_output()