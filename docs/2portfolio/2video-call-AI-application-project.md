---
title: Video Call AI Application Project
layout: default
parent: Portfolio
nav_order: 2
---

# Video Call AI Application Project
## Developed in Collaboration with the ANU TechLauncher Program

[About ANU TechLauncher](https://comp.anu.edu.au/TechLauncher/)

![Project Poster](./assets/images/portfolio/poster.jpg)

# Video Call AI: AI-Driven Real-Time Assistance

This project was developed in collaboration with **Evolutioned Pty Ltd** and through the **Australian National University TechLauncher program**, aiming to revolutionize the way people interact in remote communication through video calls.

## Project Overview

**Video Call AI** is an AI project designed to enhance video call experiences by integrating **AI-driven real-time coaching prompts**. The system utilizes advanced **Natural Language Processing (NLP)**, **Machine Learning (ML)**, and **Cloud Technologies** to analyze live conversations and provide actionable coaching advice. The project was developed to address the growing need for remote communication tools that not only facilitate video calls but also enhance the quality of interactions. By leveraging real-time visual and audio analysis, Video Call AI provides users with personalized coaching prompts during conversations, helping them improve communication and decision-making.



![Architectural Diagram](BaekCheolKim.github.io\assets\images\portfolio\architecture-diagram.jpg)

[SoW of this project](https://drive.google.com/file/d/16n2vd1aOY1eGbfnfABO5Is-Y0BlR0hyF/view?usp=drive_link)

## Key Features

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

## System Architecture

The Video Call AI project is built on a modular design with two core components:

### Video Call App
- **Technology**: Developed in **Node.js** using **Microsoft Azure Communication Services** [Azure Communication Services](https://azure.microsoft.com/en-us/services/communication-services/).
- **Functionality**: Facilitates seamless video calls with features such as **live captions** and intuitive join mechanisms.
- **Role**: Serves as the front-end interface where users initiate and participate in video calls, generating live captions that feed into the AI system.

### AI Web Service
- **Technology**: A **Python Flask-based web API** that processes live captions and generates coaching prompts using a custom **Azure OpenAI deployment** named 'CoachablePrompt' [Azure OpenAI Services](https://azure.microsoft.com/en-us/products/ai-services/openai-service/).
- **Functionality**: Analyzes conversation segments and generates real-time coaching advice, with plans to incorporate emotion detection for enhanced personalization.
- **Integration**: Enables real-time data flow between the video app and the coaching engine, ensuring low-latency prompt delivery.

The Video Call App sends live captions (and potentially emotion data in future iterations) to the AI Web Service, which processes the input and returns real-time coaching prompts to enhance the conversation.

## How It Works

1. **Setup**: The host creates a video meeting using the Video Call App and shares the invitation link with participants.
2. **Join & Interact**: Participants join the meeting via the provided link. Upon joining, they can enable live captions, which are essential for the AI coaching feature.
3. **AI-Powered Coaching**: As the conversation progresses, the live captions are sent to the AI Web Service. The AI service analyzes the conversation segments, detects emotions (planned feature), and generates real-time coaching prompts. These prompts are then displayed to the participants, providing them with actionable advice to enhance their communication and decision-making during the call.

## Technical Details

### Languages & Frameworks
- **Node.js**: Front-end and video call application, enabling robust and scalable video call functionality.
- **Python Flask**: Back-end AI web service utilizing a custom **Azure OpenAI deployment** named 'CoachablePrompt' for generating coaching prompts.
- **Microsoft Azure**: Cloud infrastructure for hosting and deployment, ensuring scalability and reliability.

### Development Tools
- **GitHub Actions**: For Continuous Integration/Continuous Deployment (CI/CD) pipelines, streamlining development and deployment processes.
- **Visual Studio Code** and **PyCharm**: For development, providing robust environments for coding and debugging.

### Key Integrations
- **Azure Communication Services**: Powers the video calling feature, enabling seamless and high-quality video interactions.
- **Azure OpenAI Services**: Hosts the 'CoachablePrompt' model for real-time coaching prompt generation, leveraging advanced NLP capabilities.

### Technical Implementation Details
The AI Web Service uses a Python-based Flask API to handle incoming conversation data. The `load_llm` function initializes the Azure OpenAI client with a specific API version (2024-02-01) and a custom endpoint, ensuring secure and efficient access to the 'CoachablePrompt' model. The `get_advice` function processes conversation segments and emotional inputs (planned) to generate coaching advice, utilizing threading for efficient handling of real-time data.

| Component | Technology | Purpose |
|-----------|------------|---------|
| Video Call App | Node.js, Azure Communication Services | Facilitates video calls with live captions |
| AI Web Service | Python Flask, Azure OpenAI ('CoachablePrompt') | Generates real-time coaching prompts |
| Cloud Infrastructure | Microsoft Azure | Ensures scalability and low-latency performance |

## Achievements

- **Improved Latency and Quality**: The coaching prompt module has been optimized to provide low-latency coaching advice for each conversational segment, significantly improving upon the initial proof of concept.
- **Real-Time Coaching Prototype**: Successfully delivered a prototype that provides actionable coaching advice during live video calls, demonstrating the feasibility of the AI coaching companion.
- **Scalable Architecture**: The system is built on a modular and scalable architecture using Microsoft Azure, ensuring it can handle increased loads and future enhancements seamlessly.

## Future Enhancements

- **Emotion Detection**:
  - Incorporate emotional insights into the advice generation process to enhance personalization, leveraging computer vision and audio analysis.
- **Domain Knowledge Integration**:
  - Use **Retrieval-Augmented Generation (RAG)** to incorporate domain-specific knowledge into coaching prompts, making them more relevant for specific industries or use cases.
- **Enhanced Conversation Segmentation**:
  - Add speaker and user ID tracking to improve the segmentation of conversational chunks, allowing for more precise and timely coaching advice.

## Collaboration with ANU TechLauncher

The project was developed as part of the ANU TechLauncher program, which connects students with real-world clients to develop innovative solutions [ANU TechLauncher Program](https://comp.anu.edu.au/TechLauncher/). This collaboration provided a unique opportunity to work with industry professionals, apply technical skills, and address real-world challenges in remote communication.

## Conclusion

The Video Call AI project represents a significant step forward in enhancing remote communication through AI-driven coaching. By combining advanced NLP, scalable cloud infrastructure, and a user-friendly video call platform, the project delivers a prototype that demonstrates the potential for real-time coaching in virtual interactions. With planned enhancements like emotion detection and domain-specific prompts, Video Call AI is poised to make a lasting impact on how people connect and collaborate remotely.
