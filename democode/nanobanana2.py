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
input_image_path = "input.jpeg"
image_to_edit = Image.open(input_image_path)

# Define the editing prompt
edit_prompt = """Smooth out wrinkles and flatten the garment.  
  Remove the background and place the garment on a pure white background.  
  Make it look like a professional product photo.  
  Maintain the natural shape of the clothing."""

# Call the API with both the image and the text prompt
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[edit_prompt, image_to_edit]
)

# Process and Save the edited image (same saving logic as above)
for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        edited_image = Image.open(BytesIO(part.inline_data.data))
        edited_image.save("shirt.png")
        print("Edited image saved as man.png")