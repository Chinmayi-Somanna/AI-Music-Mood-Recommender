# 🎵 AI Music Mood Recommender

An AI-powered web application that detects the user's mood through **facial expressions and voice** and recommends songs based on the detected emotion and selected language.

## ✨ Features

- 📷 **Facial Emotion Detection**
  - Uses the camera to capture the user's facial expression.
  - DeepFace analyzes the expression and detects the emotion.

- 🎤 **Voice Emotion Detection**
  - Captures the user's voice through the microphone.
  - Uses a Wav2Vec2-based emotion recognition model to identify the emotion.

- 🎵 **Mood-Based Music Recommendation**
  - Recommends songs according to the detected emotion.
  - Supports multiple languages.

- ▶️ **YouTube Integration**
  - Users can select a recommended song.
  - The application can open the song directly in Google Chrome.

## 🧠 Emotions Supported

The system can work with emotions such as:

- 😊 Happy
- 😢 Sad
- 😠 Angry
- 😐 Neutral
- 😨 Fear
- 🤢 Disgust
- 😲 Surprise

## 🛠️ Technologies Used

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- Flask

### AI / Machine Learning
- DeepFace
- RetinaFace
- Wav2Vec2
- Hugging Face Transformers

### Other Technologies
- OpenCV
- NumPy
- Librosa
- SoundFile
- yt-dlp

## 📂 Project Structure

```text
AI_MUSIC_MOOD_RECOMMENDER/
│
├── app.py
│
├── templates/
│   └── index.html
│
├── static/
│   └── js/
│       └── camera.js
│
└── .gitignore
