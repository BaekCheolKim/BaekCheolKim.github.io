# Llama 3.1 70B's KV cache is 320 KiB per token, an eighth of what it would be without GQA

<!-- Draft written by Claude. The numbers were checked against Table 3 of the
     Llama 3 paper and vLLM's source; rewrite it in your own words, then delete
     this comment. -->

During generation, every layer keeps the key and value vectors of every earlier token, so the KV cache grows with each token. For Llama 3.1 70B in BF16 it takes 320 KiB per token. Grouped-query attention (GQA) is the reason it is not 2.5 MiB.

Each layer stores one key vector and one value vector per KV head for each token:

```text
bytes per token = 2 × layers × KV heads × head dimension × bytes per value
```

[Table 3 of the Llama 3 paper](https://arxiv.org/abs/2407.21783) gives the 70B model 80 layers, a model dimension of 8,192, 64 attention heads and 8 key/value heads, so each head has 8,192 / 64 = 128 dimensions. In BF16 that is 2 × 80 × 8 × 128 × 2 = 327,680 bytes, or 320 KiB per token.

With multi-head attention, each of the 64 query heads would have its own KV head, eight times as many: 2.5 MiB per token. GQA lets each group of 8 query heads share one KV head.

For 8 sequences of 8,192 tokens, the workload of [Fig. 1](../../index.html#hbm) on the homepage, that is 20 GiB with GQA and 160 GiB without. 160 GiB does not fit in the 95.6 GiB of one GH200.

**Tensor parallelism divides the cache only up to the number of KV heads.** Tensor parallelism splits attention by heads, so each GPU keeps the KV heads that its query heads use. Llama 3.1 70B has 8 KV heads, so above TP 8 two GPUs need the same KV head, and vLLM keeps a copy on each. Its [`get_num_kv_heads`](https://github.com/vllm-project/vllm/blob/c2cc003c5b644095cabcd5212d2967546ce344f8/vllm/config/model.py#L1879-L1899) returns `max(1, total_num_kv_heads // tensor_parallel_size)`:

```python
layers, kv_heads, head_dim, bf16 = 80, 8, 128, 2      # Llama 3.1 70B
tokens = 8 * 8192
for tp in (1, 2, 4, 8, 16):
    heads = max(1, kv_heads // tp)                    # KV heads on each GPU
    print(tp, heads, 2 * layers * heads * head_dim * bf16 * tokens / 2**30, "GiB")
```

| TP | KV heads per GPU | KV cache per GPU |
|---:|---:|---:|
| 1 | 8 | 20 GiB |
| 2 | 4 | 10 GiB |
| 4 | 2 | 5 GiB |
| 8 | 1 | 2.5 GiB |
| 16 | 1 | 2.5 GiB |

At TP 16 each KV head is stored on two GPUs, so the 16 GPUs hold 40 GiB between them for the same 20 GiB of keys and values.
