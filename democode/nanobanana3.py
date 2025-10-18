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
# Load the image you want to edit
input_image_path = "download9.png"
image_to_edit = Image.open(input_image_path)

# Define the editing prompt
# edit_prompt = """I have few outfit combinations. Place each combination's cloths on a mannequin, side by side, keeping the original image dimensions. Remove the background and display the garments on a pure white backdrop."""
edit_prompt = """I have a outfit combinations. Place the combination's cloths on a mannequin.Remove the background and display the garments on a pure white backdrop."""

# Call the API with both the image and the text prompt
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[edit_prompt, image_to_edit]
)

# Process and Save the edited image (same saving logic as above)
for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        edited_image = Image.open(BytesIO(part.inline_data.data))
        edited_image.save("mannequins13.png")
        print("Edited image saved as mannequins13.png")