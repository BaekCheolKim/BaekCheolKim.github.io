# Settings for LLM jobs on GH200 nodes with Slingshot, layer by layer

<!-- Draft written by Claude, laid out like a cluster's site settings file and checked
     against the documentation and source code linked below. Values in < > are
     placeholders. Keep account and partition names, paths, node names and job IDs out
     of this page. Rewrite it in your own words, then delete this comment. -->

A training or RL job on a GPU cluster needs settings beyond the framework defaults: some make it faster, others prevent wrong results, hangs or full file systems. These are the settings to check first on a Slurm cluster of GH200 nodes connected by HPE Slingshot, from the scheduler down to the model. Change one at a time and measure the effect: with nccl-tests for the network, with the step time for everything else.

## Slurm

```bash
#SBATCH --exclusive          # whole nodes: no other job shares their GPUs or NICs
#SBATCH --cpus-per-task=72   # one task per GPU, with the 72 cores of its Grace CPU
#SBATCH --propagate=NONE     # don't copy the login shell's resource limits into the job
export SLURM_NETWORK=disable_rdzv_get   # only with libfabric's alt_read protocol (next section)
```

- **Cores per task.** All the threads of a task share the cores it is given: the training loop, data loading, and NCCL's CPU proxy thread, which its documentation names in the `PROXY` debug category ("the proxy thread operations"). The GH200 datasheet lists "72 Neoverse V2 Armv9 cores" per Grace CPU, so with one task per GPU each task can have all 72.
- **`--propagate=NONE`.** By default sbatch copies the submitting shell's soft resource limits into the job: "If no rlimit is specified, then all resource limits will be propagated" ([sbatch documentation](https://slurm.schedmd.com/sbatch.html)). That includes `NPROC`, the maximum number of processes, which on Linux counts threads. Login nodes often set it low, and a job that starts many threads, such as a Ray cluster, then cannot start them. With `NONE`, the compute nodes' own limits apply.

## Network: NCCL and libfabric

```bash
export NCCL_NET="AWS Libfabric"     # use the libfabric plugin, and fail at start-up without it
export FI_PROVIDER=cxi              # libfabric: only the Slingshot provider
export NCCL_IB_DISABLE=1            # NCCL: no built-in InfiniBand/RoCE transport
export NCCL_SOCKET_IFNAME=<ifaces>  # NCCL's bootstrap over the high-speed interfaces
export FI_CXI_RDZV_PROTO=alt_read   # optional; needs SLURM_NETWORK=disable_rdzv_get
# export NCCL_PROTO=^LL128          # workaround, only if nccl-tests finds wrong results
```

- **Make the plugin mandatory.** `NCCL_NET` "forces NCCL to use a specific network, for example to make sure NCCL uses an external plugin and doesn't automatically fall back on the internal IB or Socket implementation" ([NCCL environment variables](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html)). Without it, a missing plugin shows up only as a slow job; [How GPUs communicate](../networking/how-gpus-communicate.md) lists the log lines to check. `NCCL_IB_DISABLE=1` is not enough on its own, because NCCL "will instead fall back to another available transport such as IP sockets".
- **`FI_PROVIDER=cxi`** keeps libfabric from choosing a software provider such as `tcp`.
- **`NCCL_SOCKET_IFNAME`** "specifies which IP interfaces to use for communication", including NCCL's start-up exchange. Name the high-speed interfaces, not the management network.
- **`alt_read`.** The cxi provider's `FI_CXI_RDZV_PROTO` selects the protocol for large messages. Its [man page](https://ofiwg.github.io/libfabric/main/man/fi_cxi.7.html) says that "the 'alt_read' rendezvous protocol may help improve collective operation performance" and that it needs the CXI driver property `rdzv_get_en` set to 0. Slurm turns rendezvous gets off for a job with `--network=disable_rdzv_get`, which `SLURM_NETWORK` sets ("Disable rendezvous gets in Slingshot NICs", in the [srun documentation](https://slurm.schedmd.com/srun.html)). Use the pair only if your site recommends it, and measure before and after.
- **LL128.** NCCL's documentation discourages setting `NCCL_PROTO` "with the exception of disabling a specific protocol in case a bug in NCCL is suspected", and warns that "enabling LL128 on platforms that don't support it can lead to data corruption". nccl-tests checks results as well as speed. If it reports wrong values, `NCCL_PROTO=^LL128` excludes that protocol. The variable is in the documentation's "Debugging" section, whose variables "should not be used in production nor retained in scripts, or only as workaround", so remove it once a fixed NCCL is installed.
- **`FI_CXI_*` tuning.** [CSCS publishes](https://docs.cscs.ch/software/communication/nccl/) the values it uses on its GH200 system, `FI_CXI_DEFAULT_CQ_SIZE`, `FI_CXI_DEFAULT_TX_SIZE`, `FI_CXI_DISABLE_HOST_REGISTER`, `FI_CXI_RX_MATCH_MODE` and `FI_MR_CACHE_MONITOR`, as "found to give the best performance on the Alps network across a wide range of applications". Such values depend on the system's software versions. Start from the set your own site documents, and check it with nccl-tests, for correctness as well as bandwidth, before using it.

## Containers

```bash
srun --container-image=<image>.sqsh \
     --container-mounts=<code>,<data>,<scratch> \
     --no-container-mount-home ...
export UV_DEFAULT_INDEX=https://pypi.org/simple   # if the image points uv at a mirror you can't reach
```

- **Image file.** Pyxis's `--container-image` takes "an enroot URI, or a path to a squashfs file" ([Pyxis README](https://github.com/NVIDIA/pyxis)). Importing a registry image once into a `.sqsh` file on shared storage saves every job from downloading and converting it again.
- **Architecture.** A GH200's CPU is Arm, so images must be built for arm64.
- **The Slingshot stack.** Images from NVIDIA carry their own NCCL, but not the site's libfabric with the `cxi` provider or the plugin. CSCS installs libfabric into the image and uses "the AWS OFI hook to configure NCCL to use libfabric". Check the NCCL log of every new image before running long jobs with it.
- **CUDA and the driver.** An image built with a CUDA release newer than the host driver supports needs NVIDIA's forward-compatibility package, `cuda-compat-<major>-<minor>`, which exists "to allow applications built with a newer toolkit to run on older base drivers across major release families, subject to platform and GPU support" ([CUDA Compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/index.html)).
- **Mounts.** `--no-container-mount-home` means "do not bind mount the user's home directory". The container then sees only what `--container-mounts` lists, so name the code, data and scratch directories explicitly.
- **Package indexes.** An image built at another site may point uv or pip at that site's package mirror. `UV_DEFAULT_INDEX` for uv, or `PIP_INDEX_URL` for pip, points them at PyPI or at your own mirror.

## Frameworks

```bash
export CUDA_DEVICE_MAX_CONNECTIONS=1                # Megatron Core with TP or CP > 1 (see below)
export PYTORCH_ALLOC_CONF=expandable_segments:True  # fewer out-of-memory errors from fragmentation
export TORCH_NCCL_TRACE_BUFFER_SIZE=2000            # record each rank's recent collectives
export TORCH_NCCL_DUMP_ON_TIMEOUT=1                 # and write them out when one times out
export VLLM_CACHE_ROOT=<dir>                        # vLLM's compile cache
export FLASHINFER_WORKSPACE_BASE=<dir>              # FlashInfer's compiled kernels
export UV_CACHE_DIR=<dir>                           # uv's package cache
ray start ... --node-ip-address=<address on the high-speed network>
```

- **`CUDA_DEVICE_MAX_CONNECTIONS`** sets how many hardware work queues a process's CUDA streams share. With 1, all streams share one queue, so kernels are started in the order they are issued. With TP or CP above 1 on GPUs older than Blackwell, Megatron Core [stops unless it is 1](https://github.com/NVIDIA/Megatron-LM/blob/8bb413712312f66c2f140048543feea53328ca91/megatron/training/arguments.py#L1298-L1324) ("Using tensor model parallelism or context parallelism require setting the environment variable CUDA_DEVICE_MAX_CONNECTIONS to 1"). Its FSDP [needs the opposite](https://github.com/NVIDIA/Megatron-LM/blob/8bb413712312f66c2f140048543feea53328ca91/megatron/training/arguments.py#L1046-L1047) ("FSDP requires CUDA_DEVICE_MAX_CONNECTIONS > 1 or unset").
- **`expandable_segments`.** PyTorch's allocator variable is now `PYTORCH_ALLOC_CONF`, and "PYTORCH_CUDA_ALLOC_CONF is its alias" ([CUDA semantics](https://docs.pytorch.org/docs/2.15/notes/cuda.html)). The option is experimental. It helps jobs whose allocation sizes change often, such as with a changing batch size; RL with answers of varying length is one.
- **Flight recorder.** With `TORCH_NCCL_TRACE_BUFFER_SIZE` above 0 and `TORCH_NCCL_DUMP_ON_TIMEOUT=1`, PyTorch keeps each rank's recent collectives and writes them out when the watchdog times out ([ProcessGroupNCCL environment variables](https://docs.pytorch.org/docs/2.15/torch_nccl_environment_variables.html)). The dumps show which rank stopped at which collective.
- **Caches of many small files.** Compile and package caches hold many small files: vLLM's `VLLM_CACHE_ROOT` (default `~/.cache/vllm`), FlashInfer's `FLASHINFER_WORKSPACE_BASE` (default: the home directory) and uv's `UV_CACHE_DIR`. Shared file systems often cap the number of files per user or group and purge files nobody has read for a while. Put these caches where the quota and the purge rules allow it, and in the same place for every job, so that jobs reuse them.
- **Ray's node address.** Launch scripts often find each node's address by resolving its host name, and on many clusters host names resolve to a slower management network. Ray then uses that address between nodes, including for the objects its workers pass to each other. `ray start --node-ip-address` sets "the IP address of this node" ([Ray CLI](https://docs.ray.io/en/latest/cluster/cli.html)).

## The model and its memory

```text
# Megatron Core
--use-distributed-optimizer          # shard optimizer state over the data-parallel group (ZeRO-1)
--overlap-grad-reduce                # reduce gradients during the backward pass
--overlap-param-gather               # all-gather updated weights in the background
--sequence-parallel                  # with TP > 1: split the rest of each layer along the sequence
--tp-comm-overlap                    # overlap TP communication with the linear layers
--recompute-granularity selective    # recompute the memory-heavy parts of attention
--fp8-format hybrid                  # FP8 matrix multiplications through Transformer Engine
--optimizer-cpu-offload              # keep the optimizer state in CPU memory

# vLLM engine arguments, for generation
gpu_memory_utilization=<fraction>    # share of GPU memory vLLM may use
enforce_eager=False                  # keep CUDA graphs
kv_cache_dtype="fp8"                 # half the KV cache of BF16
enable_prefix_caching=True           # reuse the KV cache of shared prompt prefixes
```

- **Optimizer state** is the largest part of training memory: 12 of the [16 bytes per parameter](../parallelism/zero-bytes-per-parameter.md). The distributed optimizer shards it, and `--overlap-grad-reduce` ("overlap DDP grad reduce") and `--overlap-param-gather` ("overlap param all-gather in distributed optimizer") hide the extra communication behind computation.
- **Activations.** Sequence parallelism splits the parts of a layer that tensor parallelism leaves whole, and selective recomputation recomputes only the parts of attention that take much memory and little compute. Their paper ([Korthikanti et al., 2022](https://arxiv.org/abs/2205.05198)) reports that together they reduce "activation memory by 5x, while reducing execution time overhead from activation recomputation by over 90%". `--tp-comm-overlap` overlaps "Linear layer execution with tensor parallel communication collectives like AllGather/ReduceScatter".
- **FP8.** `--fp8-format hybrid` "enables the use of FP8 precision through Transformer Engine". Transformer Engine's hybrid format uses E4M3 in the forward pass and E5M2 in the backward pass. A GH200 runs dense FP8 at twice its BF16 rate, 1,979 against 990 TFLOPS. Compare the loss curve with a BF16 run before relying on it.
- **CPU offloading on a GH200.** NVLink-C2C makes offloading cheaper than over PCIe, but the GPU's memory is itself a NUMA node of the operating system, and NVIDIA's nvidia-smi documentation notes that under memory pressure the operating system "may resort to utilizing FB memory". Check where offloaded memory actually is with `numastat -p <pid>` before counting on the savings.
- **Generation.** `enforce_eager=False` keeps CUDA graphs, which remove most of the per-kernel launch overhead of a decode step. An FP8 KV cache takes half the memory of a BF16 one; [the KV cache TIL](../llm/kv-cache-with-gqa.md) shows how large it gets. Prefix caching pays off in RL, where many answers share one prompt.
