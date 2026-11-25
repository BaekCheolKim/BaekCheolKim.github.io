# How the five kinds of parallelism fit together

<!-- Draft written by Claude from the "Parallel Layout", "3D Parallelism" and "Pipeline
     Parallelism" notes in your glossary, checked against the sources linked below.
     Rewrite it in your own words, then delete this comment. -->

Training a large model splits the work in up to five ways: tensor, context, pipeline, data and expert parallelism, sometimes called 5D parallelism. Four of them multiply to the number of GPUs, and expert parallelism reuses GPUs that the other four have already placed. The order of the ranks decides which link each group uses. The pipeline bubble depends on the whole layout, not only on the number of stages.

## What each one splits

| Dimension | What it splits | What it sends |
|---|---|---|
| Tensor (TP) | the weight matrices of every layer | activations, in several all-reduces per layer |
| Context (CP) | every sequence, by token position | keys and values, inside attention |
| Pipeline (PP) | the layers, into consecutive stages | activations forward and their gradients backward, point to point |
| Data (DP) | the batch | gradients, once per optimizer step |
| Expert (EP) | the experts of every MoE layer | tokens to their experts and back, all-to-all |

## Four of them multiply to the GPU count

```text
GPUs = TP × CP × PP × DP
```

For example, 16,384 GPUs can run TP 8 × CP 1 × PP 16 × DP 128. For sequences 16 times as long, the same GPUs can run TP 8 × CP 16 × PP 16 × DP 8: context parallelism takes its factor from data parallelism.

## Expert parallelism reuses the same GPUs

EP does not add a factor. Take 2,048 GPUs with PP 16 and no tensor or context parallelism, so DP = 2,048 / 16 = 128 and each pipeline stage has 128 GPUs. With EP 64, the MoE layers treat those 128 GPUs as two groups of 64, and each group holds all of a layer's experts: with 256 experts, 4 per GPU. Every expert therefore exists twice per stage. Its gradients are averaged over 2 GPUs, while the gradients of the dense layers are averaged over all 128.

Megatron-Core describes the experts with a second factorization of the same GPUs, using expert tensor parallelism (ETP, which defaults to TP) and expert data parallelism (EDP). Its [`parallel_state.py`](https://github.com/NVIDIA/Megatron-LM/blob/8bb413712312f66c2f140048543feea53328ca91/megatron/core/parallel_state.py#L985-L994) computes EDP as the number of GPUs divided by ETP × EP × PP: 2,048 / (1 × 64 × 16) = 2 in this example.

## The rank order decides which link each group uses

Megatron-Core numbers ranks in the order `tp-cp-ep-dp-pp` by [default](https://github.com/NVIDIA/Megatron-LM/blob/8bb413712312f66c2f140048543feea53328ca91/megatron/core/parallel_state.py#L674), with TP varying fastest. When each node holds consecutive ranks, a TP group sits inside one node and uses NVLink, and the groups further out span nodes. Between nodes, two cases differ:

- A group that takes one GPU from each node, such as DP when TP fills the node, sends through one NIC per GPU.
- A group that contains every GPU of the nodes it spans, such as TP 8 on nodes of 4 GPUs or DP with TP 1, shares all the NICs of those nodes.

On nodes of 4 GPUs, a TP group larger than 4 has to cross the network, which is much slower than NVLink ([How GPUs communicate](../networking/how-gpus-communicate.md) has the numbers).

## The pipeline bubble depends on the whole layout

[Narayanan et al. (2021)](https://arxiv.org/abs/2104.04473) define the bubble time fraction as the idle time divided by the ideal compute time. For p stages and m micro-batches:

```text
bubble = (p − 1) / m
```

It is the same for GPipe and 1F1B; 1F1B only lowers the number of micro-batches whose activations each stage keeps. The [pipeline schedule tool](../../tools/pipeline-schedule.html) on this site shows the two schedules taking the same step time. Interleaving v chunks of layers on each GPU divides the bubble by v.

More stages look like more idle time, but m depends on the layout too. A global batch of B sequences in micro-batches of b gives each data-parallel replica m = B / (b · DP) micro-batches, and without context parallelism DP = GPUs / (TP · PP). Substituting:

```text
bubble = (PP − 1) / PP × b · GPUs / (B · TP)
```

The first factor grows from 3/4 at PP 4 toward 1. The second does not depend on PP at all. For 256 GPUs, TP 4, B = 256 and b = 1:

```python
gpus, tp, batch, micro = 256, 4, 256, 1
for pp in (4, 8, 16):
    dp = gpus // (tp * pp)
    m = batch // (micro * dp)                         # micro-batches per pipeline
    print(f"PP {pp:2}  DP {dp:2}  m {m:2}  bubble {(pp - 1) / m:.1%}")
```

```text
PP  4  DP 16  m 16  bubble 18.8%
PP  8  DP  8  m 32  bubble 21.9%
PP 16  DP  4  m 64  bubble 23.4%
```

Going from PP 4 to PP 16 cuts the weights on each GPU to a quarter and adds less than 5 percentage points of bubble, so the number of stages is chosen for memory more than for speed. The bubble shrinks only with a larger global batch, a smaller micro-batch, a larger TP or interleaving. Spreading the same batch over twice as many GPUs doubles the second factor, and the bubble with it.
