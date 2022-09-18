import ocr_tools
import numpy as np
import cv2
import pandas as pd
import os
from difflib import SequenceMatcher
from Levenshtein import distance as levenshtein_distance
import shutil
import warboard_reader


war_df = pd.read_csv('./data/raw/MD Def 18-8 Raw.csv')

print(war_df)
warboard_reader.col_to_int(war_df, 'Score')
print(war_df)