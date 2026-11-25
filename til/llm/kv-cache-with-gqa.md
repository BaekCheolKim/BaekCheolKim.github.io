# How large the KV cache is, and how GQA and tensor parallelism divide it

<!-- Draft written by Claude. The vLLM rule was checked against vLLM's source; rewrite it in
     your own words, then delete this comment. -->

During generation, every layer keeps the key and value vectors of every earlier token, so the KV cache grows with each token. Grouped-query attention (GQA) divides it by the number of query heads that share each KV head. Tensor parallelism divides it further only until each GPU holds a single KV head.

Each layer stores one key vector and one value vector per KV head for each token:

```text
bytes per token = 2 × layers × KV heads × head dimension × bytes per value
```

Take a model with 80 layers and 64 attention heads of dimension 128, in BF16. With multi-head attention, every query head has its own KV head: 2 × 80 × 64 × 128 × 2 = 2,621,440 bytes, or 2.5 MiB per token. With GQA and 8 KV heads, each shared by 8 query heads, it is 2 × 80 × 8 × 128 × 2 = 327,680 bytes, or 320 KiB per token: an eighth.

For 8 sequences of 8,192 tokens, that is 160 GiB without GQA and 20 GiB with it. 160 GiB does not fit in the 95.6 GiB of one GH200.

**Tensor parallelism divides the cache only up to the number of KV heads.** Tensor parallelism splits attention by heads, so each GPU keeps the KV heads that its query heads use. With 8 KV heads, above TP 8 two GPUs need the same KV head, and vLLM keeps a copy on each. Its [`get_num_kv_heads`](https://github.com/vllm-project/vllm/blob/c2cc003c5b644095cabcd5212d2967546ce344f8/vllm/config/model.py#L1879-L1899) returns `max(1, total_num_kv_heads // tensor_parallel_size)`:

```python
layers, kv_heads, head_dim, bf16 = 80, 8, 128, 2      # the GQA model above
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
