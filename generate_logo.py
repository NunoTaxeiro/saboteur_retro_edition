# Improved 8/16-bit Retro Pixel Art Logo Generator

import random
from PIL import Image, ImageDraw, ImageFont

# Constants
WIDTH = 64
HEIGHT = 64
BGCOLOR = (0, 0, 0)
TEXTCOLOR = (255, 215, 0)  # Gold color

# Create a new image with a given background color
image = Image.new('RGB', (WIDTH, HEIGHT), BGCOLOR)
draw = ImageDraw.Draw(image)

# Draw gold nuggets
for _ in range(5):
    x = random.randint(0, WIDTH - 10)
    y = random.randint(0, HEIGHT - 10)
    draw.ellipse((x, y, x + 10, y + 10), fill=TEXTCOLOR)

# Load a font
font = ImageFont.load_default()

# Draw pixelated text
text = 'SABOTEUR'
text_width, text_height = draw.textsize(text, font)
text_x = (WIDTH - text_width) // 2
text_y = (HEIGHT - text_height) // 2 + 10

# Draw text with a slight shadow effect
draw.text((text_x - 1, text_y - 1), text, fill=(0, 0, 0), font=font)
draw.text((text_x + 1, text_y - 1), text, fill=(0, 0, 0), font=font)
draw.text((text_x - 1, text_y + 1), text, fill=(0, 0, 0), font=font)
draw.text((text_x + 1, text_y + 1), text, fill=(0, 0, 0), font=font)
draw.text((text_x, text_y), text, fill=TEXTCOLOR, font=font)

# Save the image
image.save('saboteur_logo.png')
print('Generated logo saved as saboteur_logo.png')
