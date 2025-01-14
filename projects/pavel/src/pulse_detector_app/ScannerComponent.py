import cv2
import numpy as np
from pulse_detector_app import BPMData
from pulse_detector_app import config


class ScannerComponent:
    def __init__(self, window):
        self.window = window
        self.bufferSize = 250
        self.cap = False
        self.face = False
        self.forehead = False
        self.bpm_data = BPMData.BPMData()
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.text_color = (255, 255, 255)
        self.background_color = (20, 20, 20)
        self.flip = False

    def __scan_face_draw_text(self, frame):
        select_camera_str = "To lock new face press: N"
        end_app_str = "To quit press: ESC"

        offset = 5
        font_scale = config.RESOLUTIONS[config.USED_RESOLUTION_INDEX]['font_scale']
        text_size1 = cv2.getTextSize(select_camera_str, self.font, font_scale, 1)[0]
        text_size2 = cv2.getTextSize(end_app_str, self.font, font_scale, 1)[0]
        max_text_size = [max(text_size1[0], text_size2[0]),
                     max(text_size1[1], text_size2[1])]

        text_rectangle_size = [max_text_size[0] + 2 * offset, max_text_size[1] * 2 + offset * 3 ]
        cv2.rectangle(frame, (0, 0), text_rectangle_size, self.background_color, -1)

        text_start = [ offset, max_text_size [1] + offset]
        cv2.putText(frame, select_camera_str, text_start,
                    self.font,
                    font_scale, self.text_color, 1)

        text_start[1] += max_text_size[1] + offset
        cv2.putText(frame, end_app_str, text_start,
                    self.font,
                    font_scale, self.text_color, 1)

    def __draw_bpm(self, frame):
        font_scale = config.RESOLUTIONS[config.USED_RESOLUTION_INDEX]['font_scale']
        x, y, w, h = self.forehead
        text_str = "%d bpm" % self.bpm_data.bpm
        text_size = np.array(cv2.getTextSize(text_str, self.font, font_scale, 1)[0])
        text_rectangle_size = np.array(1.5 * text_size, dtype=int)
        offset = np.array((text_rectangle_size - text_size)/2, dtype=int)
        width_offset = 20
        pt1 = (x + w + width_offset, y + int(h / 2 - text_rectangle_size[1] / 2))
        pt2 = (pt1[0] + text_rectangle_size[0] + width_offset, pt1[1] + text_rectangle_size[1])
        cv2.rectangle(frame, pt1, pt2, self.background_color, -1)
        cv2.putText(frame, "%d bpm" % self.bpm_data.bpm, (pt1[0] + offset[0], pt2[1] - offset[1])  ,
                    self.font,
                    font_scale, self.text_color, 1)

    def set(self, cap, face, forehead, flip):
        self.cap = cap
        self.face = face
        self.forehead = forehead
        self.flip = flip

    def scan(self):
        self.__reset()

        if not self.cap:
            return

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("failed to grab frame")
                return

            if self.flip:
                frame = cv2.flip(frame, 1)

            fx, fy, fw, fh = self.forehead
            foreheadROI = frame[fy:fy + fh, fx:fx + fw, 0:3]
            foreheadROI[:, :, 0] = 0
            foreheadROI[:, :, 2] = 0

            average = np.average(foreheadROI)

            self.bpm_data.put(average)
            self.bpm_data.analyze()
            self.bpm_data.plot()

            x, y, w, h = self.face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            self.__scan_face_draw_text(frame)
            self.__draw_bpm(frame)
            self.window.draw(frame)


            k = cv2.waitKey(1)

            if k % 256 == 27:
                # ESC pressed
                print("Escape hit, closing...")
                return 0
            elif k % 256 == ord('n') or k % 256 == ord('N'):
                return 1

    def __reset(self):
        # the data are needed to be reset
        self.bpm_data = BPMData.BPMData()

