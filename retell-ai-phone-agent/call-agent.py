# Install the SDK: https://docs.retellai.com/get-started/sdk
from retell import Retell
from retell.resources.llm import LlmResponse
from retell.resources.agent import AgentResponse
from dotenv import load_dotenv
import os

load_dotenv()

retell_client = Retell(
    api_key=os.getenv("RETELL_API_KEY")
)

# {"phone_number":"+19785068675",
# "phone_number_type":"retell-twilio",
# "phone_number_pretty":"(978) 506-8675",
# "last_modification_timestamp":1723187512482}

llm: LlmResponse = retell_client.llm.create(
    begin_message="Hey I am a virtual assistant calling from Retell Hospital.",
    general_prompt="You are ...", # system prompt
    general_tools=[ # tools for the ai agent to use during the call
        {
            "type": "end_call",
            "name": "end_call",
            "description": "End the call with user only when user explicitly requests it.",
        },
    ],
    states=[
        {
            "name": "information_collection",
            "state_prompt": "You will follow the steps below to collect information...",
            "edges": [
                {
                    "destination_state_name": "appointment_booking",
                    "description": "Transition to book an appointment if the user is due for an annual checkup based on the last checkup time collected.",
                },
            ],
            "tools": [
                {
                    "type": "transfer_call",
                    "name": "transfer_to_support",
                    "description": "Transfer to the support team when user seems angry or explicitly requests a human agent",
                    "number": "+15103401579",
                },
                # {
                #     "type": "custom",
                #     "name": "get_weather",
                #     "description":
                #         "Get the current weather, called when user is asking whether of a specific city.",
                #     "parameters": {
                #         "type": "object",
                #         "properties": {
                #             "city": {
                #                 "type": "string",
                #                 "description": "The city for which the weather is to be fetched.",
                #             },
                #         },
                #         "required": ["city"],
                #     },
                #     "speak_during_execution": True,
                #     "speak_after_execution": True,
                #     "url": "http://your-server-url-here/get_weawther", #api to get weather
                # },
            ],
        },
        {
            "name": "appointment_booking",
            "state_prompt": "You will follow the steps below to book an appointment...",
            "tools": [
                {
                    "type": "book_appointment_cal",
                    "name": "book_appointment",
                    "description": "Book an annual check up when user provided name, email, phone number, and have selected a time.",
                    "cal_api_key": "cal_live_xxxxxxxxxxxx",
                    "event_type_id": 60444,
                    "timezone": "America/Los_Angeles",
                },
            ],
        },
    ],
    starting_state="information_collection",
)

print(llm)

# Create an agent and assign LLM address
agent: AgentResponse = retell_client.agent.create(
  llm_websocket_url=llm.llm_websocket_url,
  voice_id="11labs-Adrian",
  agent_name="Ryan"
)
print(agent)

# Purhcase a phone number
# phone_number: Retell.phone_number.create(
#   inbound_agent_id="oBeDLoLOeuAbiuaMFXRtDOLriTJ5tSxD", # replace with the agent id you want to assign
#   outbound_agent_id="oBeDLoLOeuAbiuaMFXRtDOLriTJ5tSxD", # replace with the agent id you want to assign
# )
# print(phone_number)

# Get call data from call id 
# call_response = Retell.call.retrieve(
#     "119c3f8e47135a29e65947eeb34cf12d",
# )
# print(call_response)