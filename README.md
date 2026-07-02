<p align="center">
  <img src="https://github.com/user-attachments/assets/effa6d94-d912-48bc-8773-3479565cc413"width="170" alt="GHERAS Logo">
</p>

<h1 align="center">
GHERAS – AI-Powered Personalized Arabic Children's Storytelling Platform
</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-Backend-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Django-REST_Framework-092E20?logo=django" alt="Django">
  <img src="https://img.shields.io/badge/React-Frontend-61DAFB?logo=react" alt="React">
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/OpenAI-LLM_%26_TTS-412991?logo=openai" alt="OpenAI">
  <img src="https://img.shields.io/badge/AI-Multimodal-orange" alt="AI">
</p>

<p align="center">
An AI-powered web platform that generates personalized Arabic children's stories with AI-generated illustrations and expressive narration to promote positive behaviors through culturally adaptive storytelling.
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/6751ab2d-67c8-4359-be34-af7aced7aafe" width="900" alt="GHERAS Interface Preview">
</p>


## Overview
GHERAS is a full-stack AI-powered web platform that generates personalized Arabic children's stories designed to reinforce positive behaviors through engaging, culturally appropriate storytelling.

The platform combines multiple artificial intelligence services including large language models for story generation, text-to-image models for illustration generation, and text-to-speech synthesis for expressive narration, to create a complete multimodal storytelling experience. Each story is personalized using child-specific attributes such as name, age, gender, appearance, interests, target behavior, story genre, and artistic style.

Built with Django REST Framework and React, GHERAS integrates AI services through a modular architecture optimized for asynchronous multimodal content generation and progressive story loading.


## Problem & Motivation

Many existing storytelling applications provide generic stories with limited personalization and insufficient emphasis on culturally relevant behavioral education. GHERAS addresses these challenges by generating personalized Arabic stories that promote positive behaviors through engaging, AI-powered storytelling.


## Key Features

- AI-powered story generation
- Personalized storytelling based on the child's profile
- AI-generated illustrations
- Expressive text-to-speech narration
- Progressive story loading
- PDF export
- Parent dashboard for story history and reading progress

## Interface Screenshots

| Home Page | Children Page |
|:------:|:--------:|
| <img src="https://github.com/user-attachments/assets/5b82324f-891b-4b26-9bba-0d8501803d85" width="450"> | <img src="https://github.com/user-attachments/assets/ceb517eb-8a94-4fce-9c5d-9fc75a5838e6" width="450"> |

| Create Story Page | Generation Progress|
|:------------:|:-------:|
| <img src="https://github.com/user-attachments/assets/e3edac1a-187f-4bf9-94b2-1e564abb98a8" width="450"> | <img src="https://github.com/user-attachments/assets/25b6852c-97d5-4118-939b-cc6879b72c83" width="450"> |


| Story Reader Page | Library Page |
|:------------:|:--------------------:|
| <img src="https://github.com/user-attachments/assets/7a794055-81d8-4abf-9555-e721bda3139b" width="450"> | <img src="https://github.com/user-attachments/assets/20ccd328-ba2d-4b41-8495-4c1010312027" width="450"> |

|Progress & Analytics Page|
|:------------:|
| <img src="https://github.com/user-attachments/assets/6c56c7d9-5d75-4c98-8bd7-836c46e80a70" width="450"> | 

## System Workflow

```mermaid
flowchart LR
    A[Parent Creates Story] --> B[Story Preferences]
    B --> C[Story Generation]
    C --> D[Illustration Generation]
    C --> E[Audio Generation]
    D --> F[Progressive Story Delivery]
    E --> F
    F --> G[Story Reader]
    G --> H[Reading Progress]
```

## System Architecture

The platform follows a modular client-server architecture that integrates a React frontend, Django REST Framework backend, PostgreSQL database, and AI services for text generation, image generation, and speech synthesis.

The following diagram illustrates the overall system architecture:
<p align="center">
<img src="https://github.com/user-attachments/assets/820b3d94-7409-48e8-97ab-a055868c2c8a" width="950">
</p>

## AI Generation Pipeline

GHERAS integrates multiple AI models to generate multimodal stories. GPT-4o mini generates the story text, Flux.2 Max produces context-aware illustrations, and GPT-4o-mini-TTS synthesizes expressive narration. The generated assets are progressively delivered to the user while remaining content is generated asynchronously in the background.

```mermaid
flowchart LR
    A[Child Profile] --> B[GPT-4o mini]
    B --> C[Story Generation]
    C --> D[Scene Extraction]
    D --> E[Flux.2 Max]
    C --> F[GPT-4o-mini-TTS]
    E --> G[Story Illustrations]
    F --> H[Audio Narration]
    G --> I[Story Assembly]
    H --> I
    I --> J[PDF Export & Story Reader]
```

## AI Model Evaluation & Selection
| Task             | Evaluated Models                                     | Selected Model      |
| ---------------- | ---------------------------------------------------- | ------------------- |
| Story Generation | GPT-4o mini, Jais, LFM2.5, Qwen                      | **GPT-4o mini**     |
| Image Generation | Flux.2 Max, GPT Image, Flux.1 Schnell, Z-Image Turbo | **Flux.2 Max**      |
| Speech Synthesis | Multiple TTS Models                                  | **GPT-4o-mini-TTS** |


## Technology Stack

| Layer | Technologies |
|------|--------------|
| Frontend | React, TypeScript, Tailwind CSS |
| Backend | Django, Django REST Framework |
| Database | PostgreSQL |
| AI Services | GPT-4o mini, Flux.2 Max, GPT-4o-mini-TTS |
| Export | PDF generation |
| Testing | Unit testing, API testing, TypeScript checking |

## Future Improvements

- Fine-tune AI models specialized in Arabic educational storytelling.
- Introduce adaptive learning paths based on children's reading progress.
- Expand the parent dashboard with advanced reading analytics, behavioral insights, and personalized story recommendations.
- Integrate a dedicated AI safety guard layer to validate generated stories and enhance content reliability.
- Allow parents to review, edit, and approve AI-generated stories before they are shared with their children.
- Add interactive story elements and voice-based conversations.


## Author

**Amjad**  & others
Bachelor's in Artificial Intelligence  
Umm Al-Qura University

## 🔒 License and Usage
©️ Copyright (c) 2026 GHERAS Project Team.
All Rights Reserved.

This repository is private and shared for portfolio review and recruitment evaluation purposes only.  

No part of this project, including but not limited to source code, documentation, reports, designs, images, videos, diagrams, or generated assets, may be copied, modified, distributed, reused, published, sublicensed, or used for academic, commercial, or personal purposes without prior written permission from the author.

