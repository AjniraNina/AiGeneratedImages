import logging
import os
import threading
import time
import requests
from flask import Flask, request
import openai

# OpenAI API key
openai.api_key = "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"

# Create necessary directories
os.makedirs('sms_responses', exist_ok=True)
os.makedirs('narratives', exist_ok=True)
os.makedirs('images', exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Flask application
app = Flask(__name__)

@app.route("/sms", methods=['POST'])
def sms_reply():
    sms_content = request.values.get('Body', None)
    if sms_content:
        with open('sms_responses/responses.txt', 'a') as file:
            file.write(sms_content + "\n")
        logging.info(f"Received SMS: {sms_content}")
    else:
        logging.error("Received SMS without content")
    return '', 200

def generate_narrative(prompt1, prompt2):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Write a single sentence that meaningfully funny and optimistic incorporates these two phrases VERBATIM about the tech and development field, you can make up a very short premise in the same sentence if it helps make it work:\n1. '{prompt1}'\n2. '{prompt2}'\nSentence:",
            max_tokens=60
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logging.error(f"Error in generating narrative: {e}")
        return None

def download_image(url, path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(path, 'wb') as file:
                file.write(response.content)
            logging.info(f"Image downloaded and saved as {path}")
        else:
            logging.error(f"Failed to download image, status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error in downloading image: {e}")

def generate_image(description):
    try:
        response = openai.Image.create(
            prompt=f"Make this into a funny or interesting cartoony image that is clearly about this text, WITOUT ANY TEXT: {description}",
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url
        if image_url:
            image_filename = f"images/{description.replace(' ', '_').replace(',', '').replace('.', '')}.jpg"
            download_image(image_url, image_filename)
            return image_filename
    except Exception as e:
        logging.error(f"Error in generating image: {e}")
        return None

def process_responses():
    while True:
        if os.path.exists('sms_responses/responses.txt'):
            with open('sms_responses/responses.txt', 'r') as file:
                responses = [line.strip() for line in file if line.strip()]

            if len(responses) >= 2:
                first_response, second_response = responses[0], responses[1]
                narrative_sentence = generate_narrative(first_response, second_response)

                if narrative_sentence:
                    with open('narratives/story.txt', 'a') as file:
                        file.write(narrative_sentence + "\n\n")
                    logging.info(f"Narrative updated: {narrative_sentence}")

                    image_filename = generate_image(narrative_sentence)
                    if image_filename:
                        logging.info(f"Image generated for narrative: {image_filename}")

                    responses = responses[2:]
                else:
                    logging.info("Waiting for a successful narrative generation...")

                with open('sms_responses/responses.txt', 'w') as file:
                    file.writelines([response + "\n" for response in responses])
            else:
                logging.info("Waiting for more SMS responses...")
                time.sleep(5)  # Wait for more messages to arrive
        else:
            logging.info("sms_responses/responses.txt not found, waiting for file creation...")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=process_responses, daemon=True).start()
    app.run(debug=True, port=80)