import pytesseract
import numpy as np
import cv2
import pandas as pd


def preprocess(input_image, mode="primary"):
    """..."""

    if mode == "primary":
        output_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        output_image = cv2.bilateralFilter(output_image, 9, 29, 29)
        _, output_image = cv2.threshold(output_image, 120, 255, cv2.THRESH_BINARY)
    elif mode == "secondary":  # Typically less accurate
        norm_img = np.zeros((input_image.shape[0], input_image.shape[1]))
        output_image = cv2.normalize(input_image, norm_img, 0, 255, cv2.NORM_MINMAX)
        output_image = cv2.threshold(output_image, 100, 255, cv2.THRESH_BINARY)[1]
        output_image = cv2.GaussianBlur(output_image, (1, 1), 0)
    else:
        print("Invalid mode")
        return 0

    return output_image


def read_image(image, content="number"):
    """..."""

    if content == "number":
        config = r'--oem 3 --psm 6 outputbase digits white'
    elif content == "text":
        config = r'--oem 3 --psm 6'
    else:
        config = r''

    return pytesseract.image_to_string(image, config=config)


def str_to_int(str):
    """Takes in a string (read with OCR) and returns its value as an int. If it is not numeric, returns -1."""


def get_coords(width):
    """Takes in the width of a screenshot and returns the appropriate set of coords and details"""

    widths = [900, 1080, 1440]
    closest_width = min(widths, key=lambda x:abs(x-width))

    if closest_width == 899:  # Joli res, TODO
        pass
    elif closest_width == 900:  # Omi res
        x_coords = {
            'Rank': (412, 440),
            'Name': (510, 660),
            'Score': (670, 740),
            'Kills': (760, 806),
            'Deaths': (846, 890),
            'Assists': (925, 975),
            'Healing': (990, 1075),
            'Damage': (1080, 1170),
            'Colour': (400, 410)
        }
        row_height = 51
        start_y = 275
    elif closest_width == 1080:  # Crank res
        x_coords = {
            'Rank': (494, 519),
            'Name': (600, 780),
            'Score': (790, 890),
            'Kills': (900, 960),
            'Deaths': (1000, 1060),
            'Assists': (1100, 1160),
            'Healing': (1180, 1280),
            'Damage': (1280, 1380),
            'Colour': (480, 490)
        }
        row_height = 60
        start_y = 324
    elif closest_width == 1440:  # TODO?
        pass
    else:  # Auto?
        pass

    return x_coords, row_height, start_y


def get_colour(input_image):
    """Takes in a cropped element of a warboard and attempts to detect the player's colour"""

    colours = {
        'dark_yellow': [13.57, 51.55, 65.00],
        'light_yellow': [16.84, 76.41, 101.03],
        'dark_green': [21.45, 41.24, 17.03],
        'light_green': [36.80,  67.93, 28.06],
        'dark_purple': [82.24,  45.3, 65.03,],
        'light_purple': [44.13, 28.51, 34.78]
    }

    avg_colour_row = np.average(input_image, axis=0)
    avg_colour = np.average(avg_colour_row, axis=0)

    # Find closest known colour
    min_diff = 1000
    detected_colour = ''
    for colour in colours:
        diff = sum(np.absolute(avg_colour - colours[colour]))
        if diff < min_diff:
            min_diff = diff
            detected_colour = colour
    
    if 'yellow' in detected_colour:
        return 'Yellow'
    elif 'green' in detected_colour:
        return 'Green'
    else:
        return 'Purple'


def read_screenshot(image, shifted=False, retry=True):
    """..."""

    num_rows = 8
    width = image.shape[0]
    x_coords, row_height, start_y = get_coords(width)

    # If screenshot is taken with rows half-scrolled, shift down by '0.4 rows'
    if shifted:
        start_y += round(row_height * 0.4)
        num_rows = 7

    screenshot_df = pd.DataFrame(columns=['Rank', 'Name', 'Score', 'Kills', 'Deaths', 'Assists', 'Healing', 'Damage', 'Colour'])
    for i in range(num_rows):
        row_data = []
        for key in x_coords:

            # Crop the image
            x1, x2 = x_coords[key]
            y1 = start_y + i * row_height
            y2 = start_y + (i + 1) * row_height
            crop_img = image[y1:y2, x1:x2]

            if key == 'Colour':
                colour = get_colour(crop_img)
                row_data.append(colour)
                continue

            # Preprocess image
            preprocessed_img = preprocess(crop_img)

            # Attempt first reading
            if key == 'Name':
                text = read_image(preprocessed_img, 'text')
            else:
                text = read_image(preprocessed_img)

            # Retry with different preprocessing if nothing found
            retried = False
            if text == "" and retry:
                retried = True
                preprocessed_img = preprocess(crop_img, mode='secondary')
                if key == 'Name':
                    text = read_image(preprocessed_img, 'text')
                else:
                    text = read_image(preprocessed_img)
            
            # Crude error checking
            if text.strip().isnumeric():
                value = int(text)
                # Look for 'improbable' values
                if (key == "Assists" or key == "Score") and value < 10:
                    text = ""
                elif (key == "Damage") and value < 1000:
                    text = ""
                
                # Look for false positive 1's
                if value == 1:
                    # Discard if OCR already had to retry with secondary mode
                    if retried:
                        text = ""
                    
                    preprocessed_img = preprocess(crop_img, mode='secondary')
                    secondary_text = read_image(preprocessed_img)
                    if secondary_text.strip().isnumeric():
                        secondary_value = int(secondary_text)
                    else:
                        secondary_value = 0

                    # If primary and secondary readings disagree, discard reading
                    if value != secondary_value:
                        text = ""

            # Store data
            if text == "":
                text = "Not Found"
            else:
                text = text.strip()
            row_data.append(text)
        
        screenshot_df.loc[len(screenshot_df)] = row_data

    return screenshot_df
