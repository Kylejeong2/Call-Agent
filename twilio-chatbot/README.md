# Twilio Chatbot

### Note from Kyle

I used a template from Pipecat to get this started. I edited some of the LLM services to get some faster responses + different apis (like groq). Overall this was a good start to learn Pipecat and how the audio frames and stuff works, but the interruption stuff is just terrible with it. I spent probably 25 total hours tinkering with all the TTS stuff and transport stuff but couldn't figure it out. If you're a genius you could probably do it, but I gave up. 
_____________________________

This project is a FastAPI-based chatbot that integrates with Twilio to handle WebSocket connections and provide real-time communication. The project includes endpoints for starting a call and handling WebSocket connections.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configure Twilio URLs](#configure-twilio-urls)
- [Running the Application](#running-the-application)
- [Usage](#usage)

## Features

- **FastAPI**: A modern, fast (high-performance), web framework for building APIs with Python 3.6+.
- **WebSocket Support**: Real-time communication using WebSockets.
- **CORS Middleware**: Allowing cross-origin requests for testing.
- **Dockerized**: Easily deployable using Docker.

## Requirements

- Python 3.10 (YOU NEED THIS)
- Docker (for containerized deployment)
- ngrok (for tunneling)
- Twilio Account

## Installation

1. **Set up a virtual environment** (optional but recommended):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Create .env**:
    create .env based on env.example

4. **Install ngrok**:
    Follow the instructions on the [ngrok website](https://ngrok.com/download) to download and install ngrok.

## Configure Twilio URLs

1. **Update the Twilio Webhook**:
    Copy the ngrok URL and update your Twilio phone number webhook URL to `http://<ngrok_url>/start_call`.

2. **Update the streams.xml**:
    Copy the ngrok URL and update templates/streams.xml with `wss://<ngrok_url>/ws`.
    * this is super important, you need to reset it everytime you restart ngrok

## Running the Application

### Using Python

1. **Run the FastAPI application**:
    ```sh
    python server.py
    ```

2. **Start ngrok**:
    In a new terminal, start ngrok to tunnel the local server:
    ```sh
    ngrok http 8765
    ```
### Using Docker

* i never used the docker container, but it should work

1. **Build the Docker image**:
    ```sh
    docker build -t twilio-chatbot .
    ```

2. **Run the Docker container**:
    ```sh
    docker run -it --rm -p 8765:8765 twilio-chatbot
    ```
## Usage

To start a call, simply make a call to your Twilio phone number. The webhook URL will direct the call to your FastAPI application, which will handle it accordingly.