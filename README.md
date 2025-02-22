# Cranky Tutor Bot  

A **Telegram bot** for language learning using **spaced repetition**, inspired by the Leitner system.

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
- **Image Upload** – Upload an image with text, and the bot extracts phrases for practice.
