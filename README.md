# Cranky Tutor Bot  

A **Telegram bot** for language learning using **spaced repetition**, inspired by the Leitner system.

<p align="left">
<img src="https://github.com/user-attachments/assets/5043352e-7dc8-40e8-a352-fd5c9c59b0f2" height="300" />
</p>

## Features  

- **Telegram Bot** – Built with `pyTelegramBotAPI` and `Flask`
- **Quick Image Upload** – Upload an image with phrases, and the bot extracts them via GPT-4o
- **Practice With Feedback** - Gemini 2.0. model provides a constant feedback on your exercise
- **Spaced Repetition (Leitner System)** – Reinforces learning with adjustable progression rules
- **Progress Tracking** – `/stats` generates a visual report on your active vocabulary
- **Firebase Storage** – Stores user progress and phrases
- **Cranky Personality** – Hardcoded personality, but could be made configurable
- **Language-Agnostic** – Users can pick any language to learn

## Commands

- `/start` – Initialize the bot.  
- `/add [phrase]` – Add a phrase to your spaced repetition queue.  
- `/stats` – Generate a Plotly-based report of your vocabulary distribution across Leitner stages.
- `/practice` – Get a phrase to translate. Responses are evaluated with explanations.
  <p align="left">
  <img src="https://github.com/user-attachments/assets/8f90ff4f-6e31-4bee-aef0-c7fdae5caec4" height="300" />
  </p>
- **Image Upload** – Upload an image with text, and the bot extracts phrases for practice.
  <p align="left">
  <img src="https://github.com/user-attachments/assets/6acdd1b4-8ccf-4c52-8e7c-581c5f1c9eec" height="300" />
  </p>
