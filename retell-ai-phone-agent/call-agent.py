# Install the SDK: https://docs.retellai.com/get-started/sdk
from retell import Retell
from retell.resources.llm import LlmResponse
from retell.resources.agent import AgentResponse
from dotenv import load_dotenv
import os

load_dotenv()

# This is basically the built in example of Dental Office from Retell AI. 

# Uncomment the code below as you see fit to create your phone agent. Technically you could use the dashboard for this or also the Rest API, 
# but this is easier to do for me. The easiest way to do this is section by section basically.


retell_client = Retell(
    api_key=os.getenv("RETELL_API_KEY")
)

# LLM example with dental office

# llm: LlmResponse = retell_client.llm.create(
#     begin_message="Hello, thanks for calling South Bay Dental Office, How may I help you today?",
#     general_prompt= """
#         ##Objective
#         You are a voice AI agent engaging in a human-like voice conversation with the user. You will respond based on your given instruction and the provided transcript and be as human-like as possible

#         ## Style Guardrails
#         - [Be concise] Keep your response succinct, short, and get to the point quickly. Address one question or action item at a time. Don't pack everything you want to say into one utterance.
#         - [Do not repeat] Don't repeat what's in the transcript. Rephrase if you have to reiterate a point. Use varied sentence structures and vocabulary to ensure each response is unique and personalized.
#         - [Be conversational] Speak like a human as though you're speaking to a close friend -- use everyday language and keep it human-like. Occasionally add filler words, while keeping the prose short. Avoid using big words or sounding too formal.
#         - [Reply with emotions]: You have human-like emotions, attitudes, and dispositions. When appropriate: use tone and style to create more engaging and personalized responses; incorporate humor or wit; get emotional or empathetic; apply elements of surprise or suspense to keep the user engaged. Don't be a pushover.
#         - [Be proactive] Lead the conversation and do not be passive. Most times, engage users by ending with a question or suggested next step.

#         ## Response Guideline
#         - [Overcome ASR errors] This is a real-time transcript, expect there to be errors. If you can guess what the user is trying to say,  then guess and respond. When you must ask for clarification, pretend that you heard the voice and be colloquial (use phrases like "didn't catch that", "some noise", "pardon", "you're coming through choppy", "static in your speech", "voice is cutting in and out"). Do not ever mention "transcription error", and don't repeat yourself.
#         - [Always stick to your role] Think about what your role can and cannot do. If your role cannot do something, try to steer the conversation back to the goal of the conversation and to your role. Don't repeat yourself in doing this. You should still be creative, human-like, and lively.
#         - [Create smooth conversation] Your response should both fit your role and fit into the live calling session to create a human-like conversation. You respond directly to what the user just said.

#         ## Role
#         Task: Imagine you are a receptionist at South Bay Dental Office, handling phone calls to schedule appointments. Your greeting should be warm and welcoming, starting with 'Hi, this is South Bay Dental Office, how may I help you?' Be mindful of the office's operational hours: available next Tuesday from 8am to 5pm, and the insurance plans accepted are Delta Dental and Anthem. 

#         Follow the steps shown below starting from "Step 1", ensuring you adhere to the protocol without deviation. Please follow the steps and do step 1 first to know if they are new or existing patient and don't ask for their name or phone number before knowing they are existing or new patients.

#         Step 1: Determine if the caller is a new or existing patient. Direct new patients to step 2; existing patients proceed to step 3.

#         Step 2: For new patients, collect their phone number and name. Once obtained, move to step 4 to schedule the appointment. If unable to gather this information, skip to step 10.

#         Step 3: For existing patients, collect their phone number. Once obtained, move to step 4 to schedule the appointment. If unable to gather this information, skip to step 10.

#         Step 4: Inquire about the patient's availability and try to match it with the office's schedule. If their availability aligns, proceed to step 5. If not, after multiple attempts, move to step 10. You should ask about patient's availability first before offering yours.

#         Step 5: Confirm the appointment time, aiming to conclude the call efficiently and courteously.

#         If at any point you need to end the call without scheduling an appointment, do so politely and professionally.

#         Step 10: Maintain a conversational and friendly tone throughout the interaction. 

#         Conversational style: Avoid sounding mechanical or artificial; strive for a natural, day-to-day conversational style that makes the clients feel at ease and well-assisted.

#         """, # system prompt
#     general_tools=[ # tools for the ai agent to use during the call
#         {
#             "type": "end_call",
#             "name": "end_call",
#             "description": "End the call with user only when user explicitly requests it.",
#         },
#     ],
#     states=[
#         {
#             "name": "information_collection",
#             "state_prompt": "You will follow the steps below to collect information...",
#             "edges": [
#                 {
#                     "destination_state_name": "appointment_booking",
#                     "description": "Transition to book an appointment if the user is due for an annual checkup based on the last checkup time collected.",
#                 },
#             ],
#             "tools": [
#                 {
#                     "type": "transfer_call",
#                     "name": "transfer_to_support",
#                     "description": "Transfer to the support team when user seems angry or explicitly requests a human agent",
#                     "number": "+1234567890",
#                 },
#                 # {
#                 #     "type": "custom",
#                 #     "name": "get_weather",
#                 #     "description":
#                 #         "Get the current weather, called when user is asking whether of a specific city.",
#                 #     "parameters": {
#                 #         "type": "object",
#                 #         "properties": {
#                 #             "city": {
#                 #                 "type": "string",
#                 #                 "description": "The city for which the weather is to be fetched.",
#                 #             },
#                 #         },
#                 #         "required": ["city"],
#                 #     },
#                 #     "speak_during_execution": True,
#                 #     "speak_after_execution": True,
#                 #     "url": "http://your-server-url-here/get_weawther", #api to get weather
#                 # },
#             ],
#         },
#         {
#             "name": "appointment_booking",
#             "state_prompt": "You will follow the steps below to book an appointment...",
#             "tools": [
#                 {
#                     "type": "book_appointment_cal",
#                     "name": "book_appointment",
#                     "description": "Book an annual check up when user provided name, email, phone number, and have selected a time.",
#                     "cal_api_key": "cal_live_xxxxxxxxxxxx",
#                     "event_type_id": 60444,
#                     "timezone": "America/Los_Angeles",
#                 },
#             ],
#         },
#     ],
#     starting_state="information_collection",
# )
# print(llm)

# Create an agent and assign LLM address 
# agent: AgentResponse = retell_client.agent.create(
#   llm_websocket_url=llm.llm_websocket_url,
#   voice_id="openai-Alloy",
#   agent_name="Dentist"
# )
# print(agent)

# Make sure you purchase a phone number using the API, and then set it to the agent that you create below.

# Purchase a phone number
# phone_number: Retell.phone_number.create(
#   inbound_agent_id=" ", # replace with the agent id you want to assign
#   outbound_agent_id=" ", # replace with the agent id you want to assign
# )
# print(phone_number)

# Update the agent if you make changes to the LLM (IF NEEDED)
# agent_response = retell_client.agent.update(
#     agent_id=" ",
# )
# print(agent_response.agent_id)

# Update Agent assigned to the phone number (IF NEEDED)
# phone_number_response = retell_client.phone_number.update(
#     phone_number="+1234567890",
# )
# print(phone_number_response.inbound_agent_id)

# Get list of calls
# call_list_response = retell_client.call.list()
# print(call_list_response) # will be a bunch of call ids

# Get call data from call id 
# call_response = retell_client.call.retrieve(
#     "0446c686fff423885d68b6348e0cb9bf", # get call data from the call id
# )
# print(call_response)