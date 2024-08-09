# Dialin example (Daily + Twilio)

### IMPORTANT: (Note from Kyle)

I only made a few adjustments to make this run on my machine. Also added custom services here so you can use Groq and stuff. 

Example project that demonstrates how to add phone number dialin to your Pipecat bots. We include examples for both Daily (`bot_daily.py`) and Twilio (`bot_twilio.py`), depending on who you want to use as a phone vendor.

- 🔁 Transport: Daily WebRTC
- 💬 Speech-to-Text: Deepgram via Daily transport
- 🤖 LLM: GPT4-o / OpenAI
- 🔉 Text-to-Speech: ElevenLabs

#### Should I use Daily or Twilio as a vendor?

If you're starting from scratch, using Daily to provision phone numbers alongside Daily as a transport offers some convenience (such as automatic call forwarding.)

If you already have Twilio numbers and workflows that you want to connect to your Pipecat bots, there is some additional configuration required (you'll need to create a `on_dialin_ready` and use the Twilio client to trigger the forward.)

You can read more about this, as well as see respective walkthroughs in our docs.

## Setup

## IMPORTANT: (Note from Kyle)

For this to work, you need to allow dailin on your room using the Daily RestAPI.
Here's how to do so:
https://docs.daily.co/guides/products/dial-in-dial-out/sip

```shell
# Install the requirements
pip install -r requirements.txt

# Setup your env
mv env.example .env
```

## Using Daily numbers

Run `bot_runner.py` to handle incoming HTTP requests:

`python bot_runner.py --host localhost`

Then target the following URL:

`POST /daily_start_bot`

For more configuration options, please consult Daily's API documentation.

## IMPORTANT: (Note from Kyle)

If you want to use Daily you HAVE to allow the phone number that you purchase to have dailin enabled.

How to get a number:
https://docs.daily.co/reference/rest-api/phone-numbers

How to enable dailin:
https://docs.daily.co/guides/products/dial-in-dial-out/dialin-pinless

## Using Twilio numbers

As above, but target the following URL:

`POST /twilio_start_bot`

* YOU NEED TO SET UP THE WEBHOOKS IN TWILIO TO POINT TO YOUR APP * 

For more configuration options, please consult Twilio's API documentation.

## Deployment example

A Dockerfile is included in this demo for convenience. Here is an example of how to build and deploy your bot to [fly.io](https://fly.io).

*Please note: This demo spawns agents as subprocesses for convenience / demonstration purposes. You would likely not want to do this in production as it would limit concurrency to available system resources. For more information on how to deploy your bots using VMs, refer to the Pipecat documentation.*

### Build the docker image

`docker build -t tag:project .`

### Launch the fly project

`mv fly.example.toml fly.toml`

`fly launch` (using the included fly.toml)

### Setup your secrets on Fly

Set the necessary secrets (found in `env.example`)

`fly secrets set DAILY_API_KEY=... OPENAI_API_KEY=... ELEVENLABS_API_KEY=... ELEVENLABS_VOICE_ID=...`

If you're using Twilio as a number vendor:

`fly secrets set TWILIO_ACCOUNT_SID=... TWILIO_AUTH_TOKEN=...`

### Deploy!

`fly deploy`

## Need to do something more advanced?

This demo covers the basics of bot telephony. If you want to know more about working with PSTN / SIP, please ping us on [Discord](https://discord.gg/pipecat).