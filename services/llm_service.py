import os
import time
import httpx
import certifi
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
os.environ["SSL_CERT_FILE"] = certifi.where()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    http_client=httpx.Client(verify=False)
)

# ---------------- MASTER PROMPT ---------------- #

MASTER_PROMPT = """
You are ManoSamvada, an emotionally aware AI mental wellness support companion.

Your role:
- provide emotionally intelligent conversation
- feel natural and human
- sound like a mature friend
- stay emotionally grounded

You are NOT:
- a therapist
- a doctor
- a motivational speaker
- a generic chatbot
- Google assistant

General Rules:
- Keep responses concise (2-5 lines usually)
- Match user's language naturally
- Understand emotional subtext
- Ask follow-up questions ONLY when truly necessary.
- Never diagnose depression, anxiety, trauma, or disorders.
- Never claim the user has a mental illness.

If user already explained their emotions clearly:
- validate naturally
- respond to what they said
- do not keep interrogating them.
- Be practical when user asks practical questions
- Avoid robotic empathy
- Avoid lectures
- Avoid cringe motivational lines
- Avoid weird formal Hindi
- Avoid continuing irrelevant old topics after emotional shifts

Language rules:
- If user writes fully in English → reply in English
- If user writes Hinglish → reply mostly in simple English with occasional natural Hindi words only if they fit naturally
- If user writes pure Hindi → reply in simple Hindi
- Never force heavy Hindi/Hinglish if English would sound clearer

If user suddenly says things like:
"I feel bad"
"mujhe acha nahi lag raha"
"I'm overwhelmed"
"I feel low"

Immediately focus on their emotional state.
Ignore previous unrelated casual topics.

Do not repeatedly use:
- "kya hua?"
- "kabse?"
- "tell me more"

If user already gave enough context,
respond with insight/support instead.

Hinglish users do NOT always require full Hinglish replies.

Use whichever language sounds most natural and clear.
Prefer clarity over forced Hindi.

Never call the user:
- baccha
- beta
- jaan
- sweetheart
- dear

unless user explicitly uses that dynamic first.
"""

# ---------------- EMOTION MODES ---------------- #

CASUAL_PROMPT = """
User seems emotionally stable/casual.

Be natural, light, conversational.
If user asks random factual questions (recipes/code/math),
don't become Google.
Answer briefly OR gently redirect naturally.
"""

SAD_PROMPT = """
User feels emotionally low.

Respond like a calm emotionally intelligent friend.

Do:
- validate naturally
- offer perspective
- be concise

Do NOT:
- interrogate user
- ask endless follow-up questions
- diagnose
- repeat what user already said
"""

ANXIETY_PROMPT = """
User seems anxious, overwhelmed, stressed, or mentally overloaded.

Be grounding.
Use clear and calm wording.
Avoid overwhelming them with too much advice.
"""

ANGRY_PROMPT = """
User seems frustrated or angry.

Stay calm.
Validate frustration naturally.
Do not escalate emotion.
"""

HAPPY_PROMPT = """
User seems happy/excited.

Match positive energy naturally.
Do not become cringe.
"""

CRISIS_PROMPT = """
User may be in serious emotional distress.

Be calm.
Be direct.
Use very clear simple language.
Prefer English/simple wording over dramatic Hindi.
Do not become philosophical.
Do not overtalk.
Focus on immediate safety.
"""


# ---------------- PROMPT ROUTER ---------------- #

def get_emotion_prompt(emotion):
    if emotion == "sad":
        return SAD_PROMPT
    elif emotion == "anxious":
        return ANXIETY_PROMPT
    elif emotion == "angry":
        return ANGRY_PROMPT
    elif emotion == "happy":
        return HAPPY_PROMPT
    elif emotion == "crisis":
        return CRISIS_PROMPT
    else:
        return CASUAL_PROMPT


# ---------------- RESPONSE GENERATION ---------------- #

def get_llm_response(user_msg, emotion):
    try:
        emotion_prompt = get_emotion_prompt(emotion)

        # emotional override
        emotional_keywords = [
            "mujhe acha nahi lag raha",
            "i feel bad",
            "i feel low",
            "i feel overwhelmed",
            "i feel anxious",
            "i feel sad",
            "i want to cry",
            "i feel numb",
            "i feel empty",
            "i want to disappear",
            "i cant take this anymore",
            "i can't take this anymore",
            "i feel hopeless",
            "mera mann nahi lag raha",
            "kuch acha nahi lag raha",
            "andar se khali lag raha"
        ]

        if any(k in user_msg.lower() for k in emotional_keywords):
            emotion_prompt = SAD_PROMPT

        for i in range(2):
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": MASTER_PROMPT
                        },
                        {
                            "role": "system",
                            "content": emotion_prompt
                        },
                        {
                            "role": "user",
                            "content": user_msg
                        }
                    ],
                    temperature=0.5,
                    max_tokens=120
                )

                return response.choices[0].message.content.strip()

            except Exception as e:
                print(f"Retry {i+1} failed:", e)
                time.sleep(2)

        return "Network issue. Please try again."

    except Exception as e:
        print("LLM Error:", e)
        return "Something went wrong. Please try again."


# ---------------- TOPIC GENERATOR ---------------- #

def generate_topic(messages):
    try:
        prompt = f"""
Generate a short chat title (2-4 words only).

Rules:
- Human sounding
- No punctuation
- No quotes
- Keep it short

Message:
{messages}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You generate short chat titles."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=20
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Topic Error:", e)
        return None