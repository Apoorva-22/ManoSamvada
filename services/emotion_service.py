from services.llm_service import client

def detect_emotion(msg):
    try:
        prompt = f"""
Classify the user's emotional state into ONLY one label:

happy
sad
angry
neutral
crisis

Message:
{msg}

Return only one word.
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an emotion classifier."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        emotion = response.choices[0].message.content.strip().lower()

        allowed = ["happy", "sad", "angry", "neutral", "crisis"]

        if emotion in allowed:
            return emotion

        return "neutral"

    except:
        return "neutral"