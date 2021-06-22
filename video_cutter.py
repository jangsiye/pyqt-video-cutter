# file open icon: https://www.flaticon.com/free-icon/open-file-button_62319
# play icon: https://www.flaticon.com/free-icon/play_727245?term=play&page=1&position=7&related_item_id=727245

import pathlib
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

file_abspath = os.path.abspath(__file__)
folder_abspath = os.path.dirname(file_abspath)

#UI파일 연결
#단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
form_class = uic.loadUiType(os.path.join(folder_abspath, "simple_video.ui"))[0]

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
        if not(img.shape[0] == target_height and img.shape[1] == target_width):  # 둘 중 하나는 같아야 함
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
        
        #Icon Load
        self.pushButton_file_open.setIcon(QIcon(os.path.join(folder_abspath, 'images', 'icon_file_open.png')))
        
        self.pushButton_play.setIcon(QIcon(os.path.join(folder_abspath, 'images', 'icon_play.png')))
        self.pushButton_play.setIconSize(QSize(32, 32))
        
        self.pushButton_scene_save.setIcon(QIcon(os.path.join(folder_abspath, 'images', 'icon_save.png')))
        self.pushButton_scene_save.setIconSize(QSize(32, 32))
        
        self.pushButton_scene_remove.setIcon(QIcon(os.path.join(folder_abspath, 'images', 'icon_remove.png')))
        self.pushButton_scene_save.setIconSize(QSize(32, 32))

        self.pushButton_forward.setIcon(QIcon(os.path.join(folder_abspath, 'images', 'icon_forward.png')))
        self.pushButton_forward.setIconSize(QSize(32, 32))
        self.pushButton_backward.setIcon(QIcon(os.path.join(folder_abspath, 'images', 'icon_backward.png')))
        self.pushButton_backward.setIconSize(QSize(32, 32))

        #버튼별 이벤트 연결
        self.pushButton_file_open.clicked.connect(self.load_video)
        self.pushButton_play.clicked.connect(self.play)
        self.pushButton_scene_init.pressed.connect(self.init_scene_setting)
        self.pushButton_scene_start.pressed.connect(self.set_scene_start_frame)
        self.pushButton_scene_end.pressed.connect(self.set_scene_end_frame)
        self.pushButton_scene_save.clicked.connect(self.save)
        self.pushButton_scene_remove.clicked.connect(self.remove_scene)
        self.pushButton_forward.clicked.connect(self.play_forward)
        self.pushButton_backward.clicked.connect(self.play_backward)

        #버튼 비활성화
        self.pushButton_play.setEnabled(False)
        self.pushButton_scene_init.setEnabled(False)
        self.pushButton_scene_start.setEnabled(False)
        self.pushButton_scene_end.setEnabled(False)
        self.pushButton_scene_save.setEnabled(False)
        self.pushButton_scene_remove.setEnabled(False)
        self.pushButton_forward.setEnabled(False)
        self.pushButton_backward.setEnabled(False)
        
        #슬라이더 비활성화 및 이벤트 연결
        self.horizontalSlider.setEnabled(False)
        self.horizontalSlider.valueChanged.connect(self.move_frame)

        #타이머 정의
        self.scene_progressbar_timer = QTimer()
        
        self.video_play_timer = QTimer()
        self.video_play_timer.timeout.connect(self.read_next_frame)
        
        self.scene_progressbar_timer.setInterval(1000/60.)
        self.scene_progressbar_timer.timeout.connect(self.draw_scene_progress_bar)
        self.scene_progressbar_timer.start()

        #키 이벤트 정의
        QShortcut(Qt.Key_Space, self, self.play)
        QShortcut(Qt.Key_Right, self, self.play_forward)
        QShortcut(Qt.Key_Left, self, self.play_backward)
        
        #씬 위젯 이벤트 연결
        self.listWidget.itemClicked.connect(self.move_scene)
    
    def video_capture_release(self):
        if self.video_capture == None:
            return None
        self.video_capture.release()
    
    def load_video(self):
        
        self.video_file = QFileDialog.getOpenFileName(self, "Open a file", folder_abspath , "video file (*.mp4 *.avi *.mkv *.MP4 *.AVI *.MKV)")[0]
        
        if len(self.video_file) == 0:
            return None
        
        self.scene_start_frame_index = 0
        self.scene_end_frame_index = 0
        
        self.video_name = Path(self.video_file).resolve().stem
        self.frame_index = 0

        self.video_capture_release()
        self.video_capture = cv2.VideoCapture(self.video_file, apiPreference=cv2.CAP_FFMPEG)
        
        if self.video_capture == None or not self.video_capture.isOpened():
            return self.video_capture_release()
   
        self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.video_num_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        
        self.video_play_timer.setInterval(1000./self.video_fps)
                
        self.horizontalSlider.blockSignals(True)
        self.horizontalSlider.setValue(0)
        self.horizontalSlider.blockSignals(False)
        
        self.horizontalSlider.setEnabled(True)
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(self.video_num_frames)
        
        self.pushButton_play.setEnabled(True)
        self.pushButton_scene_init.setEnabled(False)
        self.pushButton_scene_start.setEnabled(True)
        self.pushButton_scene_end.setEnabled(False)
        self.pushButton_scene_save.setEnabled(True)
        self.pushButton_scene_remove.setEnabled(True)
        self.pushButton_forward.setEnabled(True)
        self.pushButton_backward.setEnabled(True)
        
        self.listWidget.clear()
        self.read_next_frame()
        
    def play(self):
        if not self.pushButton_play.isEnabled():
            return None
        
        if self.video_play_timer.isActive():# 재생중이였다면
            self.pushButton_play.setIcon(QIcon(os.path.join(folder_abspath, "images", 'icon_play.png')))
            self.video_play_timer.stop()
        else: # 일시정지 상태였다면
            self.pushButton_play.setIcon(QIcon(os.path.join(folder_abspath, "images", 'icon_pause.png')))
            self.video_play_timer.start()
                   
    def init_scene_setting(self):
        self.pushButton_scene_start.setEnabled(True)
        self.pushButton_scene_end.setEnabled(False)
        self.pushButton_scene_init.setEnabled(False)
        
        
    def set_scene_start_frame(self):
        self.scene_start_frame_index = self.frame_index
        
        self.pushButton_scene_start.setEnabled(False)
        self.pushButton_scene_end.setEnabled(True)
        self.pushButton_scene_init.setEnabled(True)

    def set_scene_end_frame(self):
        self.scene_end_frame_index = self.frame_index
        self.init_scene_setting()
                
        self.listWidget.addItem(str(self.scene_start_frame_index) + "_" + str(self.scene_end_frame_index))
    
    def move_scene(self):
        #해당 씬의 시작지점으로 이동
        if self.video_play_timer.isActive():
            self.video_play_timer.stop()
        
        clicked_item = self.listWidget.currentItem().text()
        clicked_item = clicked_item.split('_')
            
        start_frame_index = int(clicked_item[0])
        
        self.frame_index = start_frame_index
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
        
        self.read_next_frame()
        
        print(str(self.listWidget.currentRow()) + " : " + self.listWidget.currentItem().text())

    def remove_scene(self):
        self.removeItemRow = self.listWidget.currentRow()
        self.listWidget.takeItem(self.removeItemRow)
        
    def save(self):       
        if self.listWidget.count() == 0:
            return None
        
        QMessageBox.question(self, 'Message', 'Image save Start!', QMessageBox.Yes)
        print('-' + self.video_name + '-')

        if self.video_play_timer.isActive():
            self.video_play_timer.stop()

        self.scene_progressbar_timer.stop()
        
        # if not os.path.isdir("./" + self.video_name):
        #     os.mkdir("./" + self.video_name)
        scene_folder = "./img"

        for item_index in range(self.listWidget.count()):
            item = self.listWidget.item(item_index).text()
            print('start ' + item)
            item = item.split('_')
            
            start_frame_index = int(item[0])
            end_frame_index = int(item[1])
            
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame_index)
            
            #scene_folder = os.path.join("./", self.video_name, "s" + format(item_index + 1, '02d'))

            # 충주 영상은 30fps
            for i in range(start_frame_index, end_frame_index):
                if not os.path.isdir(scene_folder):
                    os.mkdir(scene_folder)
                
                total_frame = end_frame_index - start_frame_index 
                
                # 10초 이하면 1fps(1초간격)로 뽑기
                # 10초 이상 20초 이하면 0.5fps(2초간격)로 뽑기
                # 20초 이상 30초 이하면 0.4fps(2.5초간격)로 뽑기
                # 30초 이상 50초 이하면 0.3fps(3.3초간격)로 뽑기
                # 50초 초과면 0.2fps(5초간격)으로 뽑기
                if total_frame < 300:
                    fps_value = 30
                elif total_frame < 600:
                    fps_value = 60
                elif total_frame < 900:
                    fps_value = 75
                elif total_frame < 1500:
                    fps_value = 100
                else:
                    fps_value = 150
                    
                if i % fps_value == 0:
                    print(str(i))
                    read_frame, frame = self.video_capture.read()
                    frame_name = self.video_name + "_f" + format(i, '05d') + ".jpg"
                    cv2.imwrite(os.path.join(scene_folder, frame_name), frame)
                else:
                    read_frame, frame = self.video_capture.read()

        QMessageBox.question(self, 'Message', 'Image save done!', QMessageBox.Yes)
        print('-END-')

        self.scene_progressbar_timer.start()
            
    def move_frame(self):
        if self.video_play_timer.isActive():
            self.video_play_timer.stop()
            
        self.frame_index = self.horizontalSlider.value()-1
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
        
        self.read_next_frame()
        
        if not self.pushButton_scene_start.isEnabled():#
            if self.frame_index < self.scene_start_frame_index:
                QMessageBox.question(self, 'Message', 'Scene setting is intialized', QMessageBox.Yes)
                self.init_scene_setting()
                
    def play_forward(self):
        if not self.pushButton_forward.isEnabled():
            return None   
            
        self.frame_index = self.horizontalSlider.value()-1
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index + 150)     # +5초
        
        read_frame, frame = self.video_capture.read()
        
        if read_frame:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = letter_box_resize(frame, (self.label_frame.width(), self.label_frame.height()))
            height, width, channels = frame.shape
            bytesPerLine = channels * width
            qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap01 = QPixmap.fromImage(qImg)
            
            self.label_frame.setPixmap(pixmap01)
            if self.frame_index > self.video_num_frames - 150:
                self.frame_index = self.video_num_frames
            else:
                self.frame_index += 150

            self.horizontalSlider.blockSignals(True)
            self.horizontalSlider.setValue(self.frame_index)
            self.horizontalSlider.blockSignals(False)
            
            self.label_frame_index.setText(str(self.frame_index)+ "/" + str(self.video_num_frames))
        
        self.video_play_timer.start()

    def play_backward(self):
        if not self.pushButton_backward.isEnabled():
            return None  

        self.frame_index = self.horizontalSlider.value()-1
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index - 150)     # -5초
        
        read_frame, frame = self.video_capture.read()
        
        if read_frame:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = letter_box_resize(frame, (self.label_frame.width(), self.label_frame.height()))
            height, width, channels = frame.shape
            bytesPerLine = channels * width
            qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap01 = QPixmap.fromImage(qImg)
            
            self.label_frame.setPixmap(pixmap01)

            if self.frame_index < 150:
                self.frame_index = 0
            else:
                self.frame_index -= 150

            self.horizontalSlider.blockSignals(True)
            self.horizontalSlider.setValue(self.frame_index)
            self.horizontalSlider.blockSignals(False)
            
            self.label_frame_index.setText(str(self.frame_index)+ "/" + str(self.video_num_frames))
        
        self.video_play_timer.start()
    
    def read_next_frame(self):
        if not self.pushButton_play.isEnabled():
            return None
        
        read_frame, frame = self.video_capture.read()
        
        if read_frame:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = letter_box_resize(frame, (self.label_frame.width(), self.label_frame.height()))
            height, width, channels = frame.shape
            bytesPerLine = channels * width
            qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap01 = QPixmap.fromImage(qImg)
            
            self.label_frame.setPixmap(pixmap01)
            self.frame_index += 1       ## 이거 건너뛰게 설정 -> 빨리감기

            self.horizontalSlider.blockSignals(True)
            self.horizontalSlider.setValue(self.frame_index)
            self.horizontalSlider.blockSignals(False)
            
            self.label_frame_index.setText(str(self.frame_index)+ "/" + str(self.video_num_frames))

    
    def draw_scene_progress_bar(self):
        if not self.pushButton_play.isEnabled():
            return None
        
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
