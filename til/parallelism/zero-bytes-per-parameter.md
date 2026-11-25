# Mixed-precision Adam keeps 16 bytes per parameter; Megatron's BF16 default keeps 18

<!-- Draft written by Claude from the "ZeRO" note in your glossary, checked against the
     sources linked below. Rewrite it in your own words, then delete this comment. -->

Before any activations, training with Adam in mixed precision keeps 16 bytes per parameter on every data-parallel GPU. ZeRO's three stages split 12, then 14, then all 16 of those bytes across the data-parallel group. Megatron-LM's default for BF16 training keeps the gradients in FP32, which raises the count to 18.

Section 3.1 of the [ZeRO paper](https://arxiv.org/abs/1910.02054) (Rajbhandari et al.) counts, for Ψ parameters, 2Ψ bytes of FP16 weights, 2Ψ bytes of FP16 gradients, and KΨ bytes of optimizer state, where K = 12 for mixed-precision Adam: an FP32 copy of the weights, the momentum and the variance, 4 bytes each. "In total, this results in 2Ψ + 2Ψ + KΨ = 16Ψ bytes of memory requirement."

With N<sub>d</sub> data-parallel GPUs, each stage shards one more of the three:

| Stage | Sharded across the GPUs | Bytes per GPU |
|---|---|---|
| Plain data parallelism | nothing | 16Ψ |
| ZeRO-1 | optimizer state | 4Ψ + 12Ψ / N<sub>d</sub> |
| ZeRO-2 | + gradients | 2Ψ + 14Ψ / N<sub>d</sub> |
| ZeRO-3 | + weights | 16Ψ / N<sub>d</sub> |

The paper's example is Ψ = 7.5B on N<sub>d</sub> = 64:

```python
psi, nd = 7.5e9, 64
for stage, per_gpu in [("plain DP", 16 * psi),
                       ("ZeRO-1", 4 * psi + 12 * psi / nd),
                       ("ZeRO-2", 2 * psi + 14 * psi / nd),
                       ("ZeRO-3", 16 * psi / nd)]:
    print(f"{stage:8} {per_gpu / 1e9:6.1f} GB")
```

```text
plain DP  120.0 GB
ZeRO-1     31.4 GB
ZeRO-2     16.6 GB
ZeRO-3      1.9 GB
```

According to the paper, stages 1 and 2 send the same volume as plain data parallelism, and stage 3 sends 50% more, because each layer's weights have to be gathered before they are used.

**Megatron-LM keeps FP32 gradients.** With `--bf16` and the default settings, Megatron-LM accumulates and all-reduces gradients in FP32 ([`arguments.py`](https://github.com/NVIDIA/Megatron-LM/blob/8bb413712312f66c2f140048543feea53328ca91/megatron/training/arguments.py#L1076-L1089)), so each parameter costs 2 + 4 + 12 = 18 bytes. Its [distributed optimizer guide](https://github.com/NVIDIA/Megatron-LM/blob/8bb413712312f66c2f140048543feea53328ca91/docs/user-guide/features/dist_optimizer.md) gives 18 bytes per parameter for BF16 parameters with FP32 gradients, or 6 + 12/d with the distributed optimizer, where d is the data-parallel size. For the same 7.5B parameters on 64 GPUs that is 46.4 GB per GPU, against ZeRO-1's 31.4 GB. [AI-Anatomy](../../work/ai-anatomy/index.md) counts training memory the same way, so in its training views the gradients take twice the memory of the BF16 weights.
