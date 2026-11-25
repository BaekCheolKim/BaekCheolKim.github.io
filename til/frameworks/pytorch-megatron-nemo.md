# PyTorch, Megatron Core and NeMo: what each layer of the training stack does

<!-- Draft written by Claude from the "PyTorch", "Megatron-LM" and "NeMo-RL" notes in your
     glossary and the projects' READMEs, read on 2026-11-25. The NeMo projects change often,
     so check the links again before publishing. Rewrite it in your own words, then delete
     this comment. -->

LLM training on NVIDIA GPUs usually runs on three layers of open-source software. PyTorch provides tensors, automatic differentiation and the calls that move data between GPUs. NVIDIA's Megatron Core builds model-parallel transformer training on PyTorch. The NeMo Framework adds recipes, checkpoint conversion and post-training, on top of Megatron Core or of PyTorch directly. When a job fails, knowing which layer does what tells you where to look.

| Layer | Projects | What it does |
|---|---|---|
| Recipes and workflows | NeMo Framework: Megatron Bridge, NeMo AutoModel, NeMo RL, NeMo Run | configurations for training specific models, Hugging Face checkpoint conversion, fine-tuning, reinforcement learning, launching jobs |
| Parallel training | Megatron Core | tensor, sequence, pipeline, context and expert parallelism; distributed optimizer and checkpoints |
| Framework | PyTorch | tensors, automatic differentiation, process groups and collectives, DDP and FSDP2 |
| Kernels and communication | cuBLAS, cuDNN, Transformer Engine; NCCL | matrix multiplications, attention, FP8; data movement between GPUs |

## PyTorch

PyTorch runs the model: tensors on the GPU, automatic differentiation for the backward pass, and the optimizers. Its `torch.distributed` package is what every layer above it uses to communicate.

- **Launch.** `torchrun` starts one process per GPU and gives each its place in the job through environment variables: `RANK`, `WORLD_SIZE`, `LOCAL_RANK` and `LOCAL_WORLD_SIZE`, plus `MASTER_ADDR` and `MASTER_PORT`, where the processes first meet ([torchrun documentation](https://docs.pytorch.org/docs/2.15/elastic/run.html)).
- **Process groups.** A process group is a set of ranks that communicate with each other. On GPUs its backend is `nccl`, and each group is one NCCL communicator. Collectives such as `all_reduce`, `all_gather_into_tensor`, `reduce_scatter_tensor` and `all_to_all_single`, and the point-to-point `send` and `recv`, run on a group.
- **Data parallelism.** `DistributedDataParallel` (DDP) keeps a full copy of the model on each GPU and all-reduces the gradients during the backward pass. FSDP2 (`fully_shard`) shards the parameters instead: it "converts model.parameters() from plain torch.Tensor to DTensor" spread over a device mesh, and gathers each layer's parameters just before they are used ([FSDP2 documentation](https://docs.pytorch.org/docs/2.15/distributed.fsdp.fully_shard.html)).
- **Other parallelism.** DTensor and `DeviceMesh` also express tensor parallelism and other layouts natively. NeMo AutoModel builds on them (below).

## Megatron Core

The [Megatron-LM repository](https://github.com/NVIDIA/Megatron-LM) holds two things. In its README's words, Megatron-LM is "a reference example that includes Megatron Core plus pre-configured training scripts", and Megatron Core is "a composable library with GPU-optimized building blocks for custom training frameworks", with "advanced parallelism strategies (TP, PP, DP, EP, and CP)" and "mixed precision support (FP16, BF16, FP8, and FP4)". It installs as `megatron-core` and is imported as `megatron.core`.

What it adds on top of PyTorch:

- Tensor-parallel layers that split weight matrices by columns or by rows, and sequence parallelism for the parts of a layer that tensor parallelism does not split.
- Pipeline schedules (1F1B and interleaved) and context parallelism.
- Mixture-of-experts layers: routers, token dispatchers and grouped matrix multiplications, with expert parallelism.
- A distributed optimizer, which shards the optimizer state over the data-parallel group as [ZeRO-1](../parallelism/zero-bytes-per-parameter.md) does, and distributed checkpoints that can be loaded into a different layout.
- One process group per kind of parallelism, in the rank order described in [How the five kinds of parallelism fit together](../parallelism/five-kinds-of-parallelism.md).

All of its communication goes through `torch.distributed`, so NCCL carries it. Its FP8 and fused transformer layers come from NVIDIA's Transformer Engine.

## NeMo Framework

NeMo is no longer one library. The [NVIDIA-NeMo organization](https://github.com/NVIDIA-NeMo) on GitHub holds separate projects, and the original NeMo repository now covers speech: its README calls it NeMo Speech and names v2.7.3, in the 26.04 NeMo container, as "the final NeMo release before the repository split". For LLM training the projects are:

| Project | What it is, in the project's own words |
|---|---|
| [Megatron Bridge](https://github.com/NVIDIA-NeMo/Megatron-Bridge) | "a PyTorch-native library … that provides pretraining, SFT and LoRA", and a "bridge, conversion, and verification layer" between Hugging Face and Megatron Core |
| [NeMo AutoModel](https://github.com/NVIDIA-NeMo/Automodel) | "a Pytorch DTensor-native SPMD open-source training library" for LLMs, VLMs, diffusion and retrieval models, with "PyTorch native FSDP2, HSDP, TP, CP, SP and PP" |
| [NeMo RL](https://github.com/NVIDIA-NeMo/RL) | "an open-source post-training library", with "efficient resource management using Ray" and "high performance with Megatron Core" |
| [NeMo Run](https://github.com/NVIDIA-NeMo/Run) | "a tool to configure, launch and manage your machine learning experiments" |

That gives two training paths. Megatron Bridge converts a Hugging Face checkpoint into Megatron Core's format and trains it with all five kinds of parallelism. AutoModel trains the Hugging Face model as it is, with PyTorch's own parallelism. NeMo RL can train with either one, and it generates the answers it learns from with an inference engine such as vLLM or SGLang.

The projects are still moving. On 2026-11-19, Megatron Bridge's README announced that "Megatron Bridge will be merged into the Megatron-LM repository".

## Where a problem usually comes from

| Symptom | Layer to look at |
|---|---|
| A collective times out, or a multi-node job runs at a fraction of the expected speed | NCCL and the network ([How GPUs communicate](../networking/how-gpus-communicate.md)) |
| The job rejects a layout, for example because TP does not divide the number of attention heads | the parallelism checks in Megatron Core |
| Out of GPU memory | the layout and the batch ([bytes per parameter](../parallelism/zero-bytes-per-parameter.md), [KV cache](../llm/kv-cache-with-gqa.md)) |
| A converted checkpoint gives wrong outputs | the checkpoint conversion (Megatron Bridge) |
