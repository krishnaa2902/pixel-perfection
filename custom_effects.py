from PIL import Image

def apply_sepia(image, sepia_factor):
    width, height = image.size
    pixel_data = image.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixel_data[x, y]

            new_r = int((r * (1 - (0.607 * sepia_factor / 100))) + (g * (0.769 * sepia_factor / 100)) + (b * (0.189 * sepia_factor / 100)))
            new_g = int((r * (0.349 * sepia_factor / 100)) + (g * (1 - (0.314 * sepia_factor / 100))) + (b * (0.168 * sepia_factor / 100)))
            new_b = int((r * (0.272 * sepia_factor / 100)) + (g * (0.534 * sepia_factor / 100)) + (b * (1 - (0.869 * sepia_factor / 100))))

            pixel_data[x, y] = (new_r, new_g, new_b)

    return image

    return image

