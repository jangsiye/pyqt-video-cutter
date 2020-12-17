import os

import sys
import cv2
import numpy as np

import PyQt5
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from pathlib import Path

#UI파일 연결
#단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
form_class = uic.loadUiType("simple_video.ui")[0]

def letter_box_resize(img, dsize):
    
    original_height, original_width = img.shape[:2]
    target_width, target_height = dsize

    ratio = min(
        float(target_width) / original_width,
        float(target_height) / original_height)
    resized_height, resized_width = [
        round(original_height * ratio),
        round(original_width * ratio)
    ]

    img = cv2.resize(img, dsize=(resized_width, resized_height))

    pad_left = (target_width - resized_width) // 2
    pad_right = target_width - resized_width - pad_left
    pad_top = (target_height - resized_height) // 2
    pad_bottom = target_height - resized_height - pad_top

    # padding
    img = cv2.copyMakeBorder(img,
                             pad_top,
                             pad_bottom,
                             pad_left,
                             pad_right,
                             cv2.BORDER_CONSTANT,
                             value=(0, 0, 0))

    try:
        if img.shape[0] != target_height and img.shape[1] != target_width:  # 둘 중 하나는 같아야 함
            raise Exception('Letter box resizing method has problem.')
    except Exception as e:
        print('Exception: ', e)
        exit(1)

    return img


#화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        
        self.video_capture = None
        
        self.pushButton_video_load.clicked.connect(self.loadVideo)
        self.pushButton_play.clicked.connect(self.play)
        self.pushButton_scene_init.clicked.connect(self.initSceneSetting)
        self.pushButton_scene_start.clicked.connect(self.setSceneStartFrameIndex)
        self.pushButton_scene_end.clicked.connect(self.setSceneEndFrameIndex)
        self.pushButton_save_all_scenes.clicked.connect(self.saveAllScenes)
        
        self.pushButton_play.setEnabled(False)
        self.pushButton_scene_init.setEnabled(False)
        self.pushButton_scene_start.setEnabled(False)
        self.pushButton_scene_end.setEnabled(False)
        self.pushButton_save_all_scenes.setEnabled(False)
        
        QShortcut(Qt.Key_Space, self, self.play)
    
    def video_capture_release(self):
        if self.video_capture == None:
            return None
        self.video_capture.release()
    
    def loadVideo(self):
        
        self.video_file = QFileDialog.getOpenFileName(self)[0]
        
        if len(self.video_file) == 0:
            return None
        
        self.scene_start_frame_index = 0
        self.scene_end_frame_index = 0
        
        self.video_name = Path(self.video_file).resolve().stem
        self.frame_index = 0

        self.video_capture_release()
        self.video_capture = cv2.VideoCapture(self.video_file, apiPreference=cv2.CAP_FFMPEG)
        
        if self.video_capture == None:
            return None
        
        if not self.video_capture.isOpened():    
            return None
        
        self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.video_num_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        
        self.video_play_timer = QTimer()
        self.video_play_timer.setInterval(1000./self.video_fps)
        self.video_play_timer.timeout.connect(self.read_next_frame)
        
        self.scene_progressbar_timer = QTimer()
        self.scene_progressbar_timer.setInterval(1000./self.video_fps)
        self.scene_progressbar_timer.timeout.connect(self.draw_scene_progress_bar)
        self.scene_progressbar_timer.start()
        
        self.play = False
        
        self.horizontalSlider.valueChanged.connect(self.showHorizontalSliderValue)
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(self.video_num_frames)
        
        self.pushButton_play.setEnabled(True)
        self.pushButton_scene_init.setEnabled(True)
        self.pushButton_scene_start.setEnabled(True)
        self.pushButton_scene_end.setEnabled(False)
        self.pushButton_save_all_scenes.setEnabled(True)
        
        self.listWidget.clear()
        self.read_next_frame()
        
        self.video_load = True

    def play(self):
        if self.play:
            self.play = False
            self.video_play_timer.stop()
        else:
            self.play = True
            self.video_play_timer.start()
    
    def initSceneSetting(self):
        self.pushButton_scene_start.setEnabled(True)
        self.pushButton_scene_end.setEnabled(False)
        
    def setSceneStartFrameIndex(self):
        self.scene_start_frame_index = self.frame_index
        self.pushButton_scene_start.setEnabled(False)
        self.pushButton_scene_end.setEnabled(True)
        
    def setSceneEndFrameIndex(self):
        self.scene_end_frame_index = self.frame_index
        self.pushButton_scene_start.setEnabled(True)
        self.pushButton_scene_end.setEnabled(False)
        
        self.listWidget.addItem(str(self.scene_start_frame_index) + "_" + str(self.scene_end_frame_index))
    
    def saveAllScenes(self):
        
        if self.play:
            self.play = False
            self.video_play_timer.stop()
        
        self.scene_progressbar_timer.stop()
        
        if not os.path.isdir("./" + self.video_name):
            os.mkdir("./" + self.video_name)
        
        for item_index in range(self.listWidget.count()):
            item = self.listWidget.item(item_index).text()
            item = item.split('_')
            
            start_frame_index = int(item[0])
            end_frame_index = int(item[1])
            
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame_index)
            
            scene_folder = os.path.join("./", self.video_name, "s" + format(item_index + 1, '02d'))
            for i in range(start_frame_index, end_frame_index):
                if not os.path.isdir(scene_folder):
                    os.mkdir(scene_folder)
                
                read_frame, frame = self.video_capture.read()
                
                frame_name = self.video_name + "_f" + format(i, '05d') + ".png"
                print(frame_name)
                cv2.imwrite(os.path.join(scene_folder, frame_name), frame)
                
            print(start_frame_index, end_frame_index)
        
        self.scene_progressbar_timer.start()
            
    def showHorizontalSliderValue(self):

        if self.play:
            self.play = False
            self.video_play_timer.stop()
            
        self.frame_index = self.horizontalSlider.value()-1
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
        
        self.read_next_frame()
        
        if not self.pushButton_scene_start.isEnabled():#
            if self.frame_index < self.scene_start_frame_index:
                QMessageBox.question(self, 'Message', 'Scene setting is intialized', QMessageBox.Yes)
                self.initSceneSetting()
            
    def read_next_frame(self):
        read_frame, frame = self.video_capture.read()
        
        if read_frame:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = letter_box_resize(frame, (self.label_frame.width(), self.label_frame.height()))
            height, width, channels = frame.shape
            bytesPerLine = channels * width
            qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap01 = QPixmap.fromImage(qImg)
            
            self.label_frame.setPixmap(pixmap01)
            self.frame_index += 1

            self.horizontalSlider.blockSignals(True)
            self.horizontalSlider.setValue(self.frame_index)
            self.horizontalSlider.blockSignals(False)
            
            self.label_frame_index.setText(str(self.frame_index)+ "/" + str(self.video_num_frames))

    
    def draw_scene_progress_bar(self):
        
        scene_progress_bar = np.zeros((self.label_scene_progress_bar.height(), self.label_scene_progress_bar.width(), 3), np.uint8)
        
        if not self.pushButton_scene_start.isEnabled():
            start_frame_index = int(self.label_scene_progress_bar.width() * (float(self.scene_start_frame_index) / self.video_num_frames))
            end_frame_index = int(self.label_scene_progress_bar.width() * (float(self.frame_index) / self.video_num_frames))
            scene_progress_bar[:, start_frame_index:end_frame_index] = [255, 255, 0]
            
        for item_index in range(self.listWidget.count()):
            item = self.listWidget.item(item_index).text()
            item = item.split('_')
            
            start_frame_index = int(self.label_scene_progress_bar.width() * (float(item[0]) / self.video_num_frames))
            end_frame_index = int(self.label_scene_progress_bar.width() * (float(item[1]) / self.video_num_frames))
            
            scene_progress_bar[:, start_frame_index:end_frame_index] = [0, 255, 0]

        height, width, channels = scene_progress_bar.shape
        bytesPerLine = channels * width
        qImg = QImage(scene_progress_bar.data, width, height, bytesPerLine, QImage.Format_RGB888)
        pixmap01 = QPixmap.fromImage(qImg)
        self.label_scene_progress_bar.setPixmap(pixmap01)
    

if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 
    
    #WindowClass의 인스턴스 생성
    myWindow = WindowClass()

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
