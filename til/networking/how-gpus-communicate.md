# How GPUs communicate: NVLink, NICs, libfabric and NCCL

<!-- Draft written by Claude from the "NCCL", "libfabric", "aws-ofi-nccl", "All-to-All" and
     "NVLink" notes in your glossary, checked against the sources linked below. Rewrite it
     in your own words, then delete this comment. -->

When a training job calls an all-reduce, PyTorch hands it to NCCL, and NCCL moves the bytes over whatever connects each pair of GPUs: NVLink inside a node, a network card (NIC) between nodes. Between nodes, NCCL either drives the NIC itself, for InfiniBand and plain TCP, or goes through a plugin. On HPE Slingshot that plugin is aws-ofi-nccl, which reaches the NIC through libfabric and its `cxi` provider.

## The layers

| Layer | What it does | Examples |
|---|---|---|
| Framework | calls collectives on a group of ranks | `torch.distributed` with the `nccl` backend |
| NCCL | runs collectives and point-to-point transfers between GPUs, choosing an algorithm and a path for each | `ncclAllReduce`, `ncclAlltoAll`, `ncclSend` and `ncclRecv` |
| Net plugin | connects NCCL's network transport to a NIC's API | built in: InfiniBand verbs and TCP sockets; as a plugin: aws-ofi-nccl |
| libfabric | one API for many kinds of NIC, with a provider for each kind | `cxi` (Slingshot), `efa` (AWS), `verbs`, `tcp`, `shm` |
| NICs and switches | move the packets | Cassini NICs and Rosetta switches (Slingshot), ConnectX NICs (InfiniBand) |

## Inside a node

- **NVLink** connects GPUs directly. A Hopper GPU has 18 NVLink links with 900 GB/s in total, 450 GB/s in each direction. With an NVSwitch, every GPU reaches every other one at that speed, and NCCL can do reductions inside the switch with its NVLS algorithms ("NVLink SHARP offload" in the [NCCL documentation](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html)). Without a switch, the GPUs are wired to each other directly and each pair gets only some of the links: 6 of 18 when four GPUs are wired all-to-all.
- **NVLink-C2C** connects the Grace CPU and the Hopper GPU inside a GH200 at "up to 900 gigabytes per second (GB/s) of total bandwidth, which is 7X higher than PCIe Gen5" ([GH200 datasheet](https://dam-cdn.nvd.orangelogic.com/AssetLink/tkno03fa645gb7f33w60rf200d330420.pdf)). It carries copies between CPU memory and GPU memory, such as offloaded optimizer state or a checkpoint on its way into HBM.
- **PCIe** connects the GPUs to the NICs in most systems. With GPUDirect RDMA, the NIC reads and writes GPU memory directly instead of staging the data in host memory.

For each pair of GPUs, NCCL picks a transport: P2P (direct copies over NVLink or PCIe), SHM (through host memory, when P2P is not possible) or NET (through a NIC).

## Between nodes

**Speeds.** Many GPU clusters give each GPU its own NIC. A 400 Gb/s NIC, such as an InfiniBand NDR card or the Cassini-2 NIC of HPE's Slingshot 400, moves 50 GB/s in each direction, a ninth of a Hopper GPU's NVLink. The first Slingshot NICs (Cassini, in Slingshot 11) run at 200 Gb/s. This gap is why tensor parallelism, which communicates several times per layer, stays inside a node.

**Several NICs per node.** NCCL runs several channels in parallel and spreads inter-node traffic over the NICs. According to the [NCCL documentation](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html), "to maximize inter-node communication performance when using multiple NICs, NCCL tries to use the same NICs when communicating between nodes". A group that contains every GPU of its nodes therefore uses all of their NICs at once, while a group with one GPU per node gets one NIC per GPU.

**How NCCL reaches the NIC.** NCCL has two networks built in: "IB" (InfiniBand verbs, which also covers RoCE) and "Socket" (TCP). For anything else, NCCL loads a net plugin, a shared library it looks for at start-up (`NCCL_NET_PLUGIN` in the documentation gives the search order). aws-ofi-nccl is the plugin for libfabric. AWS wrote it for its EFA network, and its [README](https://github.com/aws/aws-ofi-nccl) says that "most Libfabric providers should work with the plugin". For Slingshot, [CSCS's documentation](https://docs.cscs.ch/software/communication/nccl/) for its GH200 system says that "the aws-ofi-nccl plugin must be used".

**libfabric** is the OpenFabrics Interfaces library. An application asks it for an endpoint with the capabilities it needs; aws-ofi-nccl asks for "Reliable datagram endpoints (`FI_EP_RDM`) with tagged messaging". libfabric serves the request through a provider for the hardware. Its [source tree](https://github.com/ofiwg/libfabric/tree/main/prov) has providers such as `cxi` (Slingshot), `efa`, `verbs`, `tcp` and `shm`. `fi_info -p cxi` shows whether the `cxi` provider is installed and can see the NICs, `FI_PROVIDER` limits libfabric to one provider, and `FI_CXI_*` variables tune `cxi`. Sites publish values that work for them; CSCS lists its own.

## The silent fallback

If NCCL can't load the plugin, it falls back to its Socket network, and the job still runs, only far slower. Common causes are a plugin that isn't on the library path, one built for another NCCL version, or a container without the site's libfabric. Two checks catch it:

- With `NCCL_DEBUG=INFO`, NCCL logs `Using network Socket` in that case, and `Using network Libfabric` when the plugin is in use. Plugin versions 1.11 and earlier call it `AWS Libfabric`. On Slingshot, the plugin also logs `NET/OFI Selected provider is cxi`, followed by the fabric and the number of NICs it found.
- `NCCL_NET` forces a network, "to make sure NCCL uses an external plugin and doesn't automatically fall back on the internal IB or Socket implementation". `NCCL_NET="AWS Libfabric"` works with old and new plugin versions.

Containers built from NVIDIA's images bring their own NCCL but not the site's Slingshot libraries. CSCS installs libfabric into the image and loads the plugin with a container hook.

The settings for this stack on a GH200 cluster, with what each one does, are collected in [Settings for LLM jobs on GH200 nodes with Slingshot](../tuning/settings-for-gh200-and-slingshot.md).

## Collectives and what they cost

| Collective | Each rank ends with | Bytes each rank sends (ring) | nccl-tests factor | Used by |
|---|---|---|---|---|
| All-reduce | the sum of all ranks' buffers | 2(n−1)/n · S | 2(n−1)/n | gradients in plain data parallelism; tensor-parallel activations |
| Reduce-scatter | one shard of the sum | (n−1)/n · S | (n−1)/n | gradients with ZeRO; tensor parallelism with sequence parallelism |
| All-gather | every rank's shard | (n−1)/n · S | (n−1)/n | weights with ZeRO-3 or FSDP; sequence parallelism |
| All-to-all | a different block from every rank | (n−1)/n · S | (n−1)/n | MoE token dispatch and combine; Ulysses-style context parallelism |
| Broadcast | the root rank's buffer | S | 1 | initial weights |
| Send and receive | one buffer from one peer | S | — | pipeline stages; ring-style context parallelism |

S is each rank's buffer and n the number of ranks. For each call, NCCL chooses an algorithm (ring, tree, CollNet, NVLS or PAT) and a protocol from the message size, the number of ranks and the topology.

**All-to-all** is the collective of mixture-of-experts layers: every rank sends a different block to every other rank, to move tokens to the GPUs that hold their experts and back. Nothing is summed and nothing is sent twice, so no algorithm can send less than (n−1)/n of the buffer. The block sizes change every step with the router's choices, so frameworks first exchange the counts and then the data; PyTorch's `all_to_all_single` takes the split sizes. NCCL builds uneven all-to-alls from grouped `ncclSend` and `ncclRecv` calls. Since version 2.28.3 it also has `ncclAlltoAll` for equal blocks (["Added new host collective APIs: ncclAlltoAll, ncclScatter, and ncclGather"](https://docs.nvidia.com/deeplearning/nccl/release-notes/rel_2-28-3.html)). With uniform traffic, a group of n GPUs on nodes of g GPUs keeps g/n of the data inside each node, and 1 − g/n crosses the network: 7/8 for 32 GPUs on nodes of 4. Large expert-parallel groups are therefore limited by the NICs, not by NVLink.

**Bus bandwidth.** [nccl-tests](https://github.com/NVIDIA/nccl-tests/blob/master/doc/PERFORMANCE.md) reports the algorithm bandwidth S/t and the bus bandwidth, which is the algorithm bandwidth times the factor in the table. "The bus bandwidth should reflect the speed of the hardware bottleneck: NVLink, PCI, QPI, or network", so it can be compared directly with the link speeds above. A first check on a new system is `all_reduce_perf -b 8 -e 4G -f 2 -g 1` with one process per GPU on two nodes.

## Other ways GPUs communicate

- **MPI**, the standard message-passing interface of HPC, often launches the ranks and exchanges data on the CPU side. GPU-aware MPI implementations can send GPU buffers, but training frameworks send GPU data through NCCL.
- **NVSHMEM** lets CUDA kernels read and write other GPUs' memory directly (one-sided communication), and some MoE all-to-all libraries were built on it. NCCL 2.28.3 added a Device API, "an experimental device-side API to integrate NCCL communication directly into application kernels".
