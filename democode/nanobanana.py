import os
from dotenv import load_dotenv
from google import genai
from PIL import Image
from io import BytesIO

# Load your API key from the .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 1. Initialize the Client
client = genai.Client(api_key=API_KEY)

# 2. Define the Prompt
prompt = "A photorealistic image of a vintage red car parked on a misty mountain road at sunset."

# 3. Call the API to Generate the Image
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt]
)

# 4. Process and Save the Generated Image
# The generated image is returned as a part with inline_data
for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save("generated_car_image.png")
        print("Image successfully saved as generated_car_image.png")