# Batching alone does not make LLM decode compute-bound on a GH200

<!-- Draft written by Claude from the "Ridge Point" and "Memory-Bound" notes in your
     glossary, checked against NVIDIA's GH200 datasheet. Rewrite it in your own words,
     then delete this comment. -->

A GH200 has to do about 248 FLOPs per byte it reads from HBM before compute, not memory, becomes the limit. One decode step of a 70B-parameter model does about 1 FLOP per byte at batch 1 and 33 at batch 64 with 8,192-token contexts. Batching helps the matrix multiplications, but every sequence adds its own KV cache, and attention over that cache stays at a few FLOPs per byte.

**The ridge point.** [NVIDIA's GH200 datasheet](https://dam-cdn.nvd.orangelogic.com/AssetLink/tkno03fa645gb7f33w60rf200d330420.pdf) gives the 96GB HBM3 version 990 TFLOPS of dense BF16 (1,979 with sparsity) and up to 4 TB/s of memory bandwidth: 990 / 4 = 247.5 FLOPs per byte. Below that arithmetic intensity a kernel waits for memory; above it, for the tensor cores. Both figures are vendor peaks, and measured ones are lower.

**Matrix multiplications: b FLOPs per byte.** A decode step reads every weight once. With b sequences in the batch, each BF16 weight (2 bytes) takes part in b multiply-adds, which are 2b FLOPs: b FLOPs per byte. The weights alone would need a batch of about 248 to reach the ridge point.

**Attention: g FLOPs per byte, at any batch size.** Each sequence reads its own keys and values. With grouped-query attention, one KV head serves g query heads, and for each cached token it supplies a key and a value of d numbers each: 4d bytes in BF16. Each of the g query heads spends 2d FLOPs on the key (the dot product with its query) and 2d FLOPs on the value (adding it to the output with its attention weight). That is 4gd FLOPs for 4d bytes, or g FLOPs per byte. With 64 query heads and 8 KV heads, g = 8, whatever the batch size or context length.

**One decode step** of a 70B-parameter model in BF16, with the 320 KiB of KV cache per token worked out in [an earlier TIL](kv-cache-with-gqa.md) and g = 8, counting about 2 FLOPs per weight per sequence and 8 FLOPs per byte of KV cache:

```python
params, kv_per_token = 70e9, 327_680                 # 70B parameters; KV bytes per token
print(f"ridge point: {990e12 / 4e12:.1f} FLOP/byte")
for batch, context in [(1, 8192), (16, 8192), (64, 1024), (64, 8192)]:
    kv_bytes = kv_per_token * batch * context
    flops = 2 * params * batch + 8 * kv_bytes
    bytes_read = 2 * params + kv_bytes
    print(f"batch {batch:2}, context {context:5}: {flops / bytes_read:4.1f} FLOP/byte")
```

```text
ridge point: 247.5 FLOP/byte
batch  1, context  8192:  1.1 FLOP/byte
batch 16, context  8192: 14.1 FLOP/byte
batch 64, context  1024: 56.6 FLOP/byte
batch 64, context  8192: 33.1 FLOP/byte
```

At batch 64 with 8,192-token contexts, one step reads 160 GiB of KV cache and 130 GiB of weights, so the cache is the larger part of the traffic. Tensor parallelism up to the number of KV heads divides the FLOPs and the bytes alike, so the ratios stay the same on each GPU.
