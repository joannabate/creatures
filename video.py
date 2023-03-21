import cv2
import numpy as np
import pandas as pd
from data import load_data, get_start_index
import multiprocessing as mp
from time import sleep

class Video:
    def __init__(self, df, width=1360, height=768, window_name='clock'):
        self.df = df
        self.width = width
        self.height = height
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 1
        self.thickness = 1
        self.background_color = (0,0,0)
        self.window_name = window_name
        self.font_color=(0,0,255)
        self.element_lookup = {0: 'earth',
                               1: 'water',
                               2: 'air',
                               3: 'fire'}
        
    def change_brightness(self, img, value=30):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = cv2.add(v,value)
        v[v > 255] = 255
        v[v < 0] = 0
        final_hsv = cv2.merge((h, s, v))
        img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
        return img

    def create_blank(self):
        # Create black blank image
        image = np.zeros((self.height, self.width, 3), np.uint8)

        # Since OpenCV uses BGR, convert the colors before using
        rgb_color = tuple(reversed(self.background_color))

        # Fill image with color
        image[:] = rgb_color

        return image
    
    def get_bottom_text(self, i):

        current_date = self.df.loc[i.value, "Timestamp"].date()

        dates = {
            'winter solstice 1': pd.Timestamp('2022-12-21').date(),
            'spring equinox 1': pd.Timestamp('2023-03-20').date(),
            'summer solstice 1': pd.Timestamp('2023-06-21').date(),
            'autumn equinox 1': pd.Timestamp('2023-09-22').date(),
            'winter solstice 2': pd.Timestamp('2023-12-21').date()
        }

        for date_name, date in dates.items():
            if current_date < date:
                bottom_text = "%d days until %s" % ((date - current_date).days, date_name[:-2])
                break
            elif current_date == date:
                bottom_text = date_name[:-2].upper()
                break

        return bottom_text


    def run(self, i, element):

        i_last = -1
        element_last = -1
        daytime_last = None

        ft = cv2.freetype.createFreeType2()
        ft.loadFontData(fontFileName='Fondamento-Regular.ttf', id=0)

        while True:

            row = self.df.iloc[i.value]
            # If it's daytime
            if row['Direct Beam'] > 0.5:
                daytime = True
                cap = cv2.VideoCapture('videos/' + self.element_lookup[element.value] + '.mp4')
            else:
                daytime = False
                cap = cv2.VideoCapture('videos/trippy/CloudRoll.mp4')

            fps = int(cap.get(cv2.CAP_PROP_FPS))

            while cap.isOpened():
                if element.value != element_last:
                    element_last = element.value
                    break

                ret, frame = cap.read()

                if ret == True:

                    sleep(1/fps)

                    if i.value != i_last: # timestep has changed

                        row = self.df.iloc[i.value]

                        if row['Timestamp'].hour < 10:
                            padding = 25
                        else:
                            padding = 0

                        i_last = i.value

                        time_text=row['Timestamp'].strftime("%-I:%M")
                        am_pm_text =row['Timestamp'].strftime("%p").lower()
                        bottom_text = self.get_bottom_text(i)

                        if row['Direct Beam'] > 0.5:
                            daytime = True
                        else:
                            daytime = False

                        if daytime != daytime_last:
                            daytime_last = daytime
                            break

                        # If it's daytime
                        if daytime:
                            # No reduction when brightness is 1 (i.e. midday)
                            # full reduction when brightness is 0 (i.e. midnight)
                            brightness_reduction = (1 - row['Direct Beam']) * 255
                        else:
                            # Vice versa
                            brightness_reduction = row['Direct Beam'] * 255

                    # Resize frame
                    frame = cv2.resize(frame, (self.width, self.height))

                    #Adjust brightness
                    frame = self.change_brightness(frame, value=-brightness_reduction)

                    # Add in time
                    ft.putText(img=frame,
                        text=time_text,
                        org=(225+padding, 250),
                        fontHeight=150,
                        color=(255,  255, 255),
                        thickness=-1,
                        line_type=cv2.LINE_AA,
                        bottomLeftOrigin=True)
                    
                    # Add in am/pm
                    ft.putText(img=frame,
                        text=am_pm_text,
                        org=(325, 375),
                        fontHeight=100,
                        color=(255,  255, 255),
                        thickness=-1,
                        line_type=cv2.LINE_AA,
                        bottomLeftOrigin=True)
                    
                    # Add in bottom text
                    ft.putText(img=frame,
                        text=bottom_text,
                        org=(50, 550),
                        fontHeight=50,
                        color=(255,  255, 255),
                        thickness=-1,
                        line_type=cv2.LINE_AA,
                        bottomLeftOrigin=True)
                        

                    cv2.imshow(self.window_name, frame)
                    cv2.namedWindow(self.window_name, cv2.WINDOW_FULLSCREEN)
                    cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN) #Disable when on large monitor
                    # cv2.resizeWindow(self.window_name, self.width, self.height) #Enable when on large monitor

                    k = cv2.waitKey(1)
                    if k==27:    # Esc key to stop
                        cap.release()
                        cv2.destroyAllWindows()
                        return

                else:
                    break



if __name__ == "__main__":
    df = load_data(cached=True)
    i = mp.Value('i', get_start_index(df))

    my_video = Video(df)
    my_video.run(i)