---
title: Video Call AI Application Project
layout: default
parent: Portfolio
nav_order: 2
---

# This is our Video Call AI Application Project affiliated by the ANU Techlauncher

![Project Poster](assets/images/portfolio/poster-v2.1.png)

# Video Call AI: AI-Driven Real-Time Assistance

This project was developed in collaboration with **Evolutioned Pty Ltd** and the **Australian National University TechLauncher program**, aiming to revolutionize the way people interact in remote communication through video calls.

---

## Project Overview

**Video Call AI** is an innovative platform designed to enhance video call experiences by integrating **AI-driven real-time coaching prompts**. The system utilizes advanced **Natural Language Processing (NLP)**, **Machine Learning (ML)**, and **Cloud Technologies** to analyze live conversations and provide actionable coaching advice.

---

### Key Features

- **Real-Time Coaching Prompts**:
  - Automatically generates advice based on live conversations.
  - Considers conversational context and emotional tone for enhanced relevance.
  
- **Emotion Detection** *(Planned)*:
  - Improves the personalization of prompts by incorporating emotional insights.

- **Conversation Segmentation**:
  - Analyzes speaker roles and segments discussions to optimize advice timing.

- **Scalability**:
  - Hosted on **Microsoft Azure**, ensuring real-time, low-latency performance.

- **Customizable Prompts**:
  - Uses externalized prompt engineering for domain-specific advice generation.

---

## System Architecture

The project is built on a modular design with two core components:

### **Video Call App**
- Developed in **Node.js** using **Microsoft Azure Communication Services**.
- Facilitates seamless video calls with features such as **live captions** and intuitive join mechanisms.

### **AI Web Service**
- A **Python Flask-based web API** processes live captions and generates coaching prompts using **Azure OpenAI services**.
- Enables real-time data flow between the video app and the coaching engine.

---

## How It Works

1. **Setup**: The host creates a video meeting and shares the invitation link with participants.
2. **Join & Interact**: Participants join the meeting, enabling live captions and initiating video analysis.
3. **AI-Powered Coaching**: The system processes live captions and provides actionable advice, helping participants enhance communication and decision-making in real-time.

---

## Technical Details

### **Languages & Frameworks**
- **Node.js**: Front-end and video call application.
- **Python Flask**: Back-end AI web service with **GPT engine** integration.
- **Microsoft Azure**: Cloud infrastructure for hosting and deployment.

### **Development Tools**
- **GitHub Actions**: For CI/CD pipelines.
- **Visual Studio Code** and **PyCharm**: For development.

### **Key Integrations**
- **Azure Communication Services**: Powers the video calling feature.
- **Azure OpenAI Services**: Generates real-time coaching prompts.

---

## Achievements

- Significantly improved latency and quality of the coaching prompt system compared to the proof of concept.
- Delivered a prototype capable of providing **real-time coaching advice** during live conversations.
- Developed a **highly scalable architecture** with modular components for easy future enhancements.

---

## Future Enhancements

- **Emotion Detection**:
  - Incorporate emotional insights into the advice generation process to enhance personalization.

- **Domain Knowledge Integration**:
  - Use **Retrieval-Augmented Generation (RAG)** to incorporate domain-specific knowledge into coaching prompts.

- **Enhanced Conversation Segmentation**:
  - Add speaker and user ID tracking to improve the segmentation of conversational chunks.
