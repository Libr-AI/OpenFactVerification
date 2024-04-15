from openai import OpenAI
import cv2
import base64
import requests
from .logger import CustomLogger

logger = CustomLogger(__name__).getlog()


def voice2text(input, openai_key):
    # voice to input
    client = OpenAI(api_key=openai_key)
    audio_file = open(input, "rb")
    transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    return transcription.text


def image2text(input, openai_key):
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Getting the base64 string
    base64_image = encode_image(input)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_key}",
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What’s in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }

    caption = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return caption.json()["choices"][0]["message"]["content"]


def video2text(input, openai_key):
    # Read the video and convert it to pictures
    video = cv2.VideoCapture(input)

    base64Frames = []
    while video.isOpened():
        success, frame = video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))

    video.release()

    # Process the pictures with GPT4-V
    client = OpenAI(api_key=openai_key)
    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                "These are frames from a video that I want to upload. Generate a compelling description that I can upload along with the video. Only return the description after the video is fully uploaded. without any other words.",
                *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::50]),
            ],
        },
    ]
    params = {
        "model": "gpt-4-vision-preview",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 500,
    }

    result = client.chat.completions.create(**params)
    return result.choices[0].message.content


def modal_normalization(modal="text", input=None, openai_key=None):
    logger.info(f"== Processing: Modal: {modal}, Input: {input}")
    if modal == "string":
        response = str(input)
    elif modal == "text":
        with open(input, "r") as f:
            response = f.read()
    elif modal == "speech":
        response = voice2text(input, openai_key)
    elif modal == "image":
        response = image2text(input, openai_key)
    elif modal == "video":
        response = video2text(input, openai_key)
    else:
        raise NotImplementedError
    logger.info(f"== Processed: Modal: {modal}, Input: {input}")
    return response
