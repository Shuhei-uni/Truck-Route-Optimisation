from PIL import Image, ImageEnhance
import numpy as np
import os

# Initialize an empty list to store the image paths
image_paths = []

# Define the current directory
current_directory = os.path.join(os.getcwd(), 'ImagesOf100Simulations')

# Above: probably only works for jack's computer because its weird.
# note: this scans every png file.

# Loop through the files in the current directory
for filename in os.listdir(current_directory):
    # Check if the file is an image (you can add more extensions if needed)
    if filename.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
        # Get the full path of the image and add it to the list
        image_path = os.path.join(current_directory, filename)
        image_paths.append(image_path)

# Print the list of image paths (can delete after)
for path in image_paths:
    print('test')
    print(path)


# Load the first image
base_image = Image.open(image_paths[0]).convert("RGBA")

# Reduce opacity of the first image
base_image = ImageEnhance.Brightness(base_image).enhance(0.01)

# Loop through and overlay each subsequent image
for img_path in image_paths[1:]:
    img = Image.open(img_path).convert("RGBA")
    img = ImageEnhance.Brightness(img).enhance(0.01)
    
    # Overlay the image
    base_image = Image.alpha_composite(base_image, img)

# Convert to RGB and save the final composite image
final_image = base_image.convert("RGB")
final_image.save("traffic_overlay.png") #saves in the main 263Part2 folder
final_image.show()
