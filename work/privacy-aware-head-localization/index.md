---
# A case study. The lines between the two "---" fill the box at the top of the page:
# summary, period, role, team, stack and links ("Label | URL" pairs separated by ";").
# Every field is optional; lines starting with # are comments.
# date: the date used to sort this entry in "Latest" (YYYY-MM-DD).
title: Privacy-aware head localization
summary: A model that predicts where people's heads are from images that show only their bodies, so that a robot's camera could avoid recording faces. It reaches 0.63 precision and 0.71 recall on CrowdHuman.
date: 2024-11-01
period: 2024, Australian National University
team: Four students; names and individual contributions are in the report
role: Pre-processed the dataset, trained the models on a GPU cluster server, prepared the video and co-wrote the report
stack: PyTorch, YOLO11, YOLO11-Pose, ResNet, CrowdHuman
links: Report (PDF, 8 pages) | report.pdf
---

## Problem

A robot's camera records the faces of the people it passes. Masking faces after capture still stores the raw images first, where they can be stolen or misused before they are processed.

## Approach

The method predicts each person's head box from an image in which only bodies are visible, so that a camera controller could avoid capturing faces:

1. A pre-trained YOLO11 model detects body boxes. Boxes with IoU above 0.5 against the ground truth are kept.
2. A pre-trained YOLO11-Pose model extracts keypoints from each body crop.
3. A multi-layer perceptron maps the keypoints and the body box to a head box.

The baseline replaces the keypoints with ResNet embeddings of the body crop.

## Data and training

CrowdHuman annotates every person with a head box, a visible-region box and a full-body box. Each image was resized to 960×576, and every pixel above the bottom edge of the lowest head box was set to black, so the model sees bodies only.

Both models were trained on one GeForce RTX 3090 with Adam (learning rate 1×10⁻³), batch size 32, for 15 epochs, with a Smooth L1 loss on the head-box coordinates. The pre-trained detectors were frozen.

## Results

A prediction counts as correct when its IoU with the ground-truth head box is at least 0.20.

| Model | Precision | Recall | AP | F1 |
|---|--:|--:|--:|--:|
| ResNet-based (baseline) | 0.38 | 0.60 | 0.23 | 0.46 |
| YOLO11-Pose-based | 0.63 | 0.71 | 0.45 | 0.67 |

The keypoint model is better on every metric. A lower IoU threshold raises all three of its scores:

| IoU threshold | Precision | Recall | AP |
|---|--:|--:|--:|
| 0.10 | 0.68 | 0.75 | 0.51 |
| 0.15 | 0.64 | 0.72 | 0.48 |
| 0.20 | 0.63 | 0.71 | 0.45 |

## Limits

- Head accuracy depends on the predicted body boxes: a wrong or partial body box gives a wrong head box.
- The pre-trained detectors were not fine-tuned for this task.
- An IoU threshold of 0.20 is lenient. Detection benchmarks such as PASCAL VOC use 0.50.
- The dataset was filtered by the number of people per image, which limits how well the model handles dense crowds.

<!-- Check before publishing: section 3.1.2 of the report says images with 7 or fewer people were
     filtered out; sections 5.2 and 5.3 describe the filter as a maximum number of people.
     State in the last bullet which one you applied. -->
