---
# The CV page, published at /cv.html.
# To make a PDF, open the page in a browser and print it; the site header,
# footer and this note are left out of the printout.
# The line "# Baek C. Kim" below is the title at the top of the page.
summary: CV of Baek C. Kim, AI Application Analyst (AI/HPC).
---

# Baek C. Kim

AI Application Analyst (AI/HPC) · [baekcheolkim.github.io](https://baekcheolkim.github.io/) · [github.com/BaekCheolKim](https://github.com/BaekCheolKim) · [LinkedIn](https://www.linkedin.com/in/baekcheolkim/)

<!-- Add an email address and your city to the line above if you want them on the CV. -->

I analyze how LLM training and inference map onto GPU clusters: memory residency, parallel layouts and collective communication.

## Experience

**AI Application Analyst (AI/HPC)** · KISTI Supercomputing Center, Daejeon, South Korea · Sep 2026 – present

- Model per-GPU memory residency for LLM training and inference.
- Evaluate parallel layouts (data/ZeRO/FSDP, tensor, pipeline, expert and context parallelism) for multi-node GPU clusters.
- Estimate collective-communication volume between GPUs and nodes to inform layout choices.

**Network Engineer (Data Center)** · KT Cloud, Seoul, South Korea · Jun 2026 – Aug 2026

- Configured and managed the data-center network.
- Monitored the network and troubleshot faults.
- Installed cabling.
- Provided customer support.

## Projects

**[AI-Anatomy](work/ai-anatomy/index.md)** · 2026

- Built a web page that computes per-GPU memory, data flow and collective volumes for Llama 3.1 8B, 70B and 405B, Mixtral 8x7B and DeepSeek-V3 on NVIDIA GH200 nodes, from published model configs and a measured hardware specification.
- Counted parameters matrix by matrix from each config; the totals match the published counts.

**[Privacy-aware head localization](work/privacy-aware-head-localization/index.md)** · Australian National University, 2024

- Predicted head boxes from images that show only bodies, with YOLO11-Pose keypoints and an MLP: 0.63 precision and 0.71 recall on CrowdHuman, against 0.38 and 0.60 for a ResNet baseline.
- Pre-processed the dataset and trained the models on a GPU cluster server, in a team of four.

**[Video Call AI](work/video-call-ai/index.md)** · ANU TechLauncher, with Evolutioned Pty Ltd

- Worked in a team of seven on a prototype that generates coaching prompts from live call captions: a TypeScript and Node.js call app on Azure Communication Services and a Flask service on Azure OpenAI.

<!-- Add your own part of the Video Call AI work. -->

## Education

**Master of Machine Learning and Computer Vision**, Australian National University · Feb 2023 – Feb 2025

- ANU+ Award for leadership and community engagement.

<!-- Add earlier degrees here. -->

## Skills

PyTorch, Hugging Face Transformers, Python, Docker, Azure, MLflow, Git

<!-- Add the HPC tools you use, for example Slurm, NCCL or Nsight Systems. -->
