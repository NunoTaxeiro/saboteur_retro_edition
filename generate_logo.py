from PIL import Image, ImageDraw, ImageFont

# Create a new image with a white background
width, height = 800, 200
image = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(image)

# Load a font
font = ImageFont.load_default()

# Draw text onto the image
text = 'Saboteur'
text_width, text_height = draw.textsize(text, font=font)

# Calculate position for the text to be centered
position = ((width - text_width) // 2, (height - text_height) // 2)
draw.text(position, text, fill='gold', font=font)

# Draw gold nuggets around the text (simple circles)
for _ in range(10):
    x = random.randint(0, width)
    y = random.randint(0, height)
    draw.ellipse((x-10, y-10, x+10, y+10), fill='gold')

# Save the image as a PNG file
image.save('saboteur_logo.png')

print('Logo generated and saved as saboteur_logo.png')
