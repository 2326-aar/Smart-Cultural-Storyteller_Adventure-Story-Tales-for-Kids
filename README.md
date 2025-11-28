# Smart Cultural Storyteller

A Flask web application that generates cultural stories with AI-powered text, comic-style images, and audio narration.

## Features

- **AI Story Generation**: Uses Gemini 2.0 Flash API to create cultural stories in 6 chunks
- **Comic-Style Images**: Generates visual illustrations for each story chunk using Pollinations.AI
- **Audio Narration**: Creates TTS audio for the complete story
- **Interactive UI**: Hover animations on images, responsive design with Bootstrap
- **Story Management**: Save stories to SQLite database and share them
- **Multi-language Support**: Generate stories in various languages

## Setup Instructions

1. **Install Dependencies**:


app.py                          # Main application
models.py                       # Database functions  
templates/
├── base.html                   # Base template
├── index.html                  # Home page
├── generate_new.html           # Story generation page
├── stories.html                # Stories list  
├── story.html                  # Individual story view
static/
├── css/
│   ├── style.css              # Main styling
│   └── audio-player.css       # Audio player styles
├── js/
│   └── main.js                # Main JavaScript
├── images/                    # Generated images (auto-created)
└── audio/                     # Generated audio (auto-created)
requirements.txt               # Dependencies
.env                          # Environment variables
stories.db                    # Database (auto-created)
