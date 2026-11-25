# What nvidia-smi's 97,871 MiB means on a GH200

<!-- Draft written by Claude from AI-Anatomy's hardware.js (your measurement of
     memory.total) and NVIDIA's nvidia-smi documentation. Before you publish it,
     run these on a GH200 node and check that this note still matches:
       nvidia-smi -i 0 --query-gpu=memory.total --format=csv,noheader
       nvidia-smi -i 0 -q -d MEMORY
       numactl -H
     If numactl -H does not list the GPU memory as a node without CPUs, delete
     the last section. Then delete this comment. -->

NVIDIA sells the GPU in the GH200 nodes I work with as "GH200 96GB HBM3", and nvidia-smi reports a total of 97,871 MiB for it. The two numbers use different units, and neither is the amount of memory a program can allocate.

```console
$ nvidia-smi -i 0 --query-gpu=memory.total --format=csv,noheader
97871 MiB
```

**Units.** nvidia-smi's MiB is 2<sup>20</sup> bytes:

```python
>>> total = 97871 * 2**20
>>> total, total / 2**30, total / 1e9
(102625181696, 95.5771484375, 102.625181696)
```

The total is 95.6 GiB, or 102.6 GB in decimal units. A decimal 96 GB would be 91,553 MiB, less than nvidia-smi reports, so the "96GB" on the datasheet only makes sense as 96 GiB, which is 98,304 MiB. nvidia-smi's total is 433 MiB below that.

**The total is more than a program can allocate.** `nvidia-smi -q -d MEMORY` splits the total into Reserved, Used and Free. The [nvidia-smi documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html) says that "the driver may also reserve a small amount of memory for internal use, even without active work on the GPU". Each process then creates a CUDA context, and libraries such as NCCL and cuBLAS allocate their own workspaces. [AI-Anatomy](../../work/ai-anatomy/index.md) sets aside 1 GiB for all of that. The 1 GiB is an estimate, not a measurement.

**On a GH200, Linux manages this memory.** The GPU's HBM is a NUMA node of the operating system; `numactl -H` lists it as a node with memory and no CPUs. For such systems the same documentation page says that "the accuracy of FB memory utilization provided by nvidia-smi depends on the memory accounting of the operating system", and that "pages allocated from FB memory are not released even after the process terminates". Used and Free can therefore be wrong, for example right after a job ends. The total does not depend on what has run, so plan with the total minus Reserved, the CUDA context and the library workspaces.
