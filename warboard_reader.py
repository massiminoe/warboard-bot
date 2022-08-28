"""
...

31/07/2022
"""

import ocr_tools
import numpy as np
import cv2
import pandas as pd
import os
from difflib import SequenceMatcher
from Levenshtein import distance as levenshtein_distance
import shutil


MAX_NOT_FOUND = 10
SAME_STRING_THRESHOLD = 0.8  # For matching read names with known player names


pd.options.mode.chained_assignment = None  # default='warn'

def similar(a, b):
    """String similarity function"""

    lev_dist = levenshtein_distance(a, b)
    if lev_dist == 1:
        return 0.9
    elif lev_dist == 2:
        return 0.8
    
    return SequenceMatcher(None, a, b).ratio()


def get_num_not_found(screenshot_df):
    """Counts the number of 'Not Found' entries in an image's pd.DataFrame."""

    columns = ['Rank', 'Name', 'Score', 'Kills', 'Deaths', 'Assists', 'Healing', 'Damage']
    num_not_found = 0
    for col in columns:
        num_not_found += screenshot_df[screenshot_df[col] == "Not Found"].shape[0]

    return num_not_found


def read_war_data(war_name: str, printing: bool = False, postprocess: bool = True):
    
    # Get all image files
    folder_name = os.path.join("data", war_name)
    path = os.path.join(os.getcwd(), folder_name)
    files = os.listdir(path)
    images = []
    for file in files:
        if file.endswith(".jpg") or file.endswith(".png"):
            images.append(file)

    csv_filename = os.path.join(path, war_name + " Raw.csv")

    print(f'\n{folder_name}\n')
    print(f'{len(images)} images found.')

    # Attempt to read images
    war_df = pd.DataFrame(columns=['Rank', 'Name', 'Score', 'Kills', 'Deaths', 'Assists', 'Healing', 'Damage', 'Colour'])
    for count, image in enumerate(images):
        print(f'Reading image #{count + 1}')
        filename = os.path.join(path, image)

        # Read Image
        img = cv2.imread(filename)
        screenshot_df = ocr_tools.read_screenshot(img)
        num_not_found = get_num_not_found(screenshot_df)

        # Diagnostics
        if printing:
            print(screenshot_df)
        print(f'{num_not_found} values not found')

        # See if reading should be retried with shift enabled
        shifted_num_not_found = 10000  # +inf equivalent
        if num_not_found > MAX_NOT_FOUND:
            print('Re-reading with shift enabled')
            shifted_df = ocr_tools.read_screenshot(img, True)
            shifted_num_not_found = get_num_not_found(shifted_df)
            if printing:
                print(shifted_df)
            print(f'{shifted_num_not_found} values not found')
            
        # Select best reading and add to war_df
        if shifted_num_not_found < num_not_found:
            war_df = pd.concat([war_df, shifted_df])
        else:
            war_df = pd.concat([war_df, screenshot_df])
        
        print()

    # Postprocessing
    if postprocess:

        # Clean up names by looking for close matches in a known list
        names_filename = "known_players.txt"
        names_file = open(names_filename, 'r')
        names = names_file.readlines()

        for row in war_df.itertuples():
            name = row[2]

            max_similarity = 0
            max_name = name
            for known_name in names:
                known_name = known_name.strip()
                similarity = similar(name, known_name)
                if similarity > max_similarity:
                    max_similarity = similarity
                    max_name = known_name

            if max_similarity >= SAME_STRING_THRESHOLD and max_similarity != 1:
                print(f'Replaced {name} with {max_name} | ({max_similarity})')
                war_df.replace(name, max_name, inplace=True)

        # Remove duplicates
        war_df.drop_duplicates(subset=['Name'], inplace=True)

        # Replace 'Not Found' healing values with 0, score values with -1
        war_df['Healing'].replace('Not Found', 0, inplace=True)
        war_df['Score'].replace('Not Found', -1, inplace=True)
        war_df['Score'] = war_df['Score'].astype('int64')

        # Sort by score
        war_df.sort_values(by=['Score'], ascending=False, inplace=True)

        # Replace score column using score sorting
        for i in range(war_df.shape[0]):
            war_df['Rank'].iloc[i] = i + 1

        # Fix '.0' issue by converting to int64
        war_df.to_csv(csv_filename, index=False)
        war_df = pd.read_csv(csv_filename)
        for col in war_df:
            if war_df[col].dtype == 'float64':
                war_df[col] = war_df[col].astype('int64')

    print(war_df)
    war_df.to_csv(csv_filename, index=False)

    # Save a copy in /data/raw
    dst = os.path.join(os.getcwd(), "data", "raw", f'{war_name} Raw.csv')
    shutil.copyfile(csv_filename, dst)


