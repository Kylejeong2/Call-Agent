from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
from openai import OpenAI
from dotenv import load_dotenv
from langchain.llms import GPT4All
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_client = Client(
    account_sid, auth_token
)

# Initialize GPT-4 Mini model
openai = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# Initialize Langchain conversation
conversation = ConversationChain(
    llm=openai,
    memory=ConversationBufferMemory()
)

@app.route("/answer", methods=['POST'])
def answer_call():
    """Respond to incoming phone calls with a brief message."""
    # Start our TwiML response
    resp = VoiceResponse()

    # Read a message aloud to the caller
    resp.say("Welcome to the chatbot. What would you like to ask?", voice='alice')
    
    # Listen for the caller's input
    resp.gather(input='speech', action='/process_speech', method='POST')

    return str(resp)

@app.route("/process_speech", methods=['POST'])
def process_speech():
    # Get the user's speech input
    user_speech = request.values.get('SpeechResult', '')

    # Get response from GPT-4 Mini using Langchain
    response = conversation.predict(input=user_speech)

    # Create a TwiML response
    resp = VoiceResponse()
    resp.say(response, voice='alice')
    print(response)

    # Ask if the user has another question
    resp.gather(input='speech', action='/process_speech', method='POST')

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)