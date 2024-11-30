from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  # Импортируем CORS
import cv2
import numpy as np
import easyocr
import pygetwindow as gw
#import pyautogui
from io import BytesIO
from PIL import ImageGrab
#import pywintypes
#import pypiwin32
import win32gui
import win32con
import win32ui
import win32api
import keyboard
import threading
import ctypes
from ctypes import wintypes

import keras_ocr
from io import BytesIO

# Определение структуры RECT
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG)
    ]

app = Flask(__name__)
CORS(app)  # Включаем CORS для всего приложения

reader = easyocr.Reader(['en', 'ru'])

# Горячие клавиши
hotkeys = {
    'list_windows': 'win+c',
    'active_window': 'ctrl+win+c',
    'recognize_window': 'ctrl+shift+{}',  # Для окон по индексам
}

def capture_window_screenshot(window_title):
    
    # Получаем окно по заголовку
    window = gw.getWindowsWithTitle(window_title)

    if not window:
        print("Окно не найдено.")
        return None

    # Берем первое найденное окно
    window = window[0]



    # Используем Windows API для захвата содержимого скрытого окна
    hwnd = window._hWnd  # Получаем дескриптор окна (handle)

    
    # Получаем размеры окна
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        print("Окно не найдено.")
        return None
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    width = int((right - left)*1.5)
    height = int((bottom - top)*1.5)
    
    print(f"FindWindow {hwnd = }, {width = }, {height = }")
    
    #rect = RECT()
    # Получение координат окна
    
    #ctypes.windll.user32.SwitchToThisWindow(hwnd, True)


    #is_visible = ctypes.windll.user32.IsWindowVisible(hwnd)
    #if not is_visible:
    #    print("Окно скрыто. Показываем...")
    #ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_RESTORE)
    #ctypes.windll.user32.SwitchToThisWindow(hwnd, True)

    #ctypes.windll.user32.SwitchToThisWindow(hwnd, False)
    #ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_SHOWNA)

    # Активируем окно
    #ctypes.windll.user32.SetForegroundWindow(hwnd)
    #print("Окно развернуто и активировано.")

    #lpwndpl = 0
    #res = ctypes.windll.user32.GetWindowPlacement(hwnd, lpwndpl)
    #print(f"{lpwndpl = }")
    #ctypes.windll.user32.EnableWindow(hwnd, True)
    if ctypes.windll.user32.IsIconic(hwnd):
        print("Окно свёрнуто")
        ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
        #ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_RESTORE)
        #ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_SHOWNA)
        #ctypes.windll.user32.SetForegroundWindow(hwnd)
        #time.sleep(2)
        # Получаем координаты и размеры окна
        width, height = max(width, int(window.width*1.5)), max(height, int(window.height*1.5))
        #width = 912
        #height = 279
        ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_RESTORE)
        ctypes.windll.user32.CloseWindow(hwnd)
        ctypes.windll.user32.ShowWindow(hwnd, win32con.SWP_HIDEWINDOW)
        #ctypes.windll.user32.SwitchToThisWindow(hwnd, False)
    else:
        width, height = max(width,int(window.width*1.5)), max(height,int(window.height*1.5))
    print(f"{hwnd = }, {width = }, {height = }")   

    # Получаем хэндл устройства контекста (DC) окна
    hdc = win32gui.GetWindowDC(hwnd)
    if hdc is None:
        print("Не удалось получить контекст устройства.")
        return None
    # Создаем объект для получения изображения
    hdc_mem = win32ui.CreateDCFromHandle(hdc)
    #print(f"{hdc_mem = }")
    cDC = hdc_mem.CreateCompatibleDC()
    #hdc_mem.CreateCompatibleDC()

    # Создаем пустое изображение
    try:
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(hdc_mem, width, height)
    except Exception as e:
        print(f"Ошибка при создании изображения: {e}")
        return None

    # Пытаемся выбрать битмап в контексте
    try:
        cDC.SelectObject(bitmap)
        #hdc_mem.SelectObject(bitmap)
    except Exception as e:
        print(f"Ошибка при выборе битмапа: {e}")
        #hdc_mem.DeleteDC()
        cDC.DeleteDC()
        hdc_mem.DeleteDC()
        win32gui.ReleaseDC(hwnd, hdc)
        return None

    # Копируем изображение из окна в битмап
    try:
        cDC.BitBlt((0, 0), (width, height), hdc_mem, (0, 0), win32con.SRCCOPY)
        #result = ctypes.windll.user32.PrintWindow(hwnd, cDC.GetSafeHdc(), 1)
        result = 1
        if result != 1:
            print("Не удалось захватить содержимое окна.")
            cDC.DeleteDC()
            hdc_mem.DeleteDC()
            ctypes.windll.user32.ReleaseDC(hwnd, hdc)
            return None
    except Exception as e:
        print(f"Ошибка при копировании изображения: {e}")
        cDC.DeleteDC()
        hdc_mem.DeleteDC()
        win32gui.ReleaseDC(hwnd, hdc)
        return None

    # Извлекаем изображение в numpy массив
    try:
        signed_array = bitmap.GetBitmapBits(True)
        img_array = np.frombuffer(signed_array, dtype=np.uint8)
        img_array = img_array.reshape((height, width, 4))  # BGRA изображение
    except Exception as e:
        print(f"Ошибка при извлечении изображения: {e}")
    
    # Получаем данные изображения
    signed_array = bitmap.GetBitmapBits(True)
    img_array = np.frombuffer(signed_array, dtype=np.uint8)
    img_array = img_array.reshape((height, width, 4))

    # Освобождаем ресурсы
    hdc_mem.DeleteDC()
    win32gui.ReleaseDC(hwnd, hdc)

    # Преобразуем в изображение OpenCV
    img = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)

    return img

pipeline = keras_ocr.pipeline.Pipeline()

def recognize_text_with_overlay(image):
    # Используем модель для распознавания текста
    # Результат возвращает список строк (каждая строка - это кортеж: [bbox, текст])
    prediction_groups = pipeline.recognize([image])
    
    # Делаем копию изображения для нанесения прямоугольников
    overlay = image.copy()

    text_data = []

    for text_group in prediction_groups[0]:
        bbox, text = text_group
        top_left = tuple(map(int, bbox[0]))  # Верхний левый угол
        bottom_right = tuple(map(int, bbox[2]))  # Нижний правый угол

        # Рисуем прямоугольник вокруг текста
        cv2.rectangle(overlay, top_left, bottom_right, (0, 255, 0), 2)
        # Добавляем текст на изображение
        cv2.putText(overlay, text, (top_left[0], top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # Сохраняем данные о тексте (для дальнейшего использования)
        text_data.append({
            "text": text,
            "coordinates": {"top_left": top_left, "bottom_right": bottom_right},
        })

    return overlay, text_data

def recognize_text_with_overlay_eocr(image):
    # Преобразуем изображение в серое для улучшения распознавания
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #enhanced_image = cv2.equalizeHist(gray_image)
    #blurred_image = cv2.GaussianBlur(enhanced_image, (5, 5), 0)
    # Улучшаем контрастность с помощью адаптивного порогового значения
    #_, binary_image = cv2.threshold(enhanced_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    binary_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 11, 2)

    #kernel = np.ones((3, 3), np.uint8)
    #dilated_image = cv2.dilate(binary_image, kernel, iterations=1)

    # Распознаем текст
    results = reader.readtext(binary_image)
    #results = reader.readtext(dilated_image)
    
    # Группируем текст по строкам, основываясь на координатах
    grouped_text = []
    line = []
    prev_bottom = None

    for (bbox, text, prob) in results:
        top_left = tuple(map(int, bbox[0]))
        bottom_right = tuple(map(int, bbox[2]))

        # Определяем расстояние между строками
        if prev_bottom is None or abs(top_left[1] - prev_bottom) < 10:  # Текст на одной линии
            line.append((text, top_left, bottom_right))  # Добавляем в текущую строку
        else:
            # Если расстояние между строками больше, считаем, что это новая строка
            grouped_text.append(line)  # Сохраняем строку
            line = [(text, top_left, bottom_right)]  # Начинаем новую строку

        prev_bottom = bottom_right[1]

    # Не забываем добавить последнюю строку
    if line:
        grouped_text.append(line)

    # Создаем изображение с оверлеем (только с прямоугольниками, без текста)
    overlay = image.copy()
    
    text_data = []
    for line in grouped_text:
        line_text = " ".join([item[0] for item in line])  # Собираем текст из блоков строки
        for text, top_left, bottom_right in line:
            # Рисуем прямоугольник вокруг каждого блока текста
            cv2.rectangle(overlay, top_left, bottom_right, (0, 255, 0), 2)
        
            # Сохраняем данные о тексте
            text_data.append({
                "text": text,
                "coordinates": {"top_left": top_left, "bottom_right": bottom_right},
            })

    # Возвращаем оверлей с прямоугольниками и текстовые данные с координатами
    return overlay, text_data

def list_windows():
    # Получаем список окон
    windows = [title for title in gw.getAllTitles() if title]
    
    # Если вызывается при старте, просто выводим в консоль
    print("Available windows:")
    for idx, title in enumerate(windows):
        print(f"{idx}: {title}")
    
    return windows

@app.route('/list_windows', methods=['GET'])
def list_windows_endpoint():
    # Возвращаем список окон как JSON
    windows = list_windows()
    return jsonify(windows)

@app.route('/capture_and_recognize', methods=['POST'])
def capture_and_recognize():
    data = request.json
    window_title = data.get('window_title')
    if not window_title:
        return jsonify({'error': 'Window title is required'}), 400
    image = capture_window_screenshot(window_title)
    if image is None:
        return jsonify({'error': 'Window not found'}), 404

    overlay, text_data = recognize_text_with_overlay(image)

    # Преобразуем изображение для отправки
    _, buffer = cv2.imencode('.png', overlay)
    io_buf = BytesIO(buffer)

    return jsonify({
        "image": io_buf.getvalue().decode('latin1'),  # Для передачи изображения как строки
        "text_data": text_data  # Координаты и текст
    })

# Добавление горячих клавиш
def setup_hotkeys():
    def list_windows_hotkey():
        windows = [title for title in gw.getAllTitles() if title]
        print("Active windows:")
        for idx, title in enumerate(windows):
            print(f"{idx}: {title}")

    def active_window_hotkey():
        active_window = gw.getActiveWindow()
        if not active_window:
            print("No active window detected.")
            return

        text = capture_and_recognize_active_window(active_window.title)
        print(f"Recognized text: {text}")

    def recognize_specific_window(idx):
        windows = [title for title in gw.getAllTitles() if title]
        if idx >= len(windows):
            print(f"No window with index {idx}")
            return

        window_title = windows[idx]
        text = capture_and_recognize_active_window(window_title)
        print(f"Recognized text for {window_title}: {text}")

    # Настройка горячих клавиш
    keyboard.add_hotkey(hotkeys['list_windows'], list_windows_hotkey)
    keyboard.add_hotkey(hotkeys['active_window'], active_window_hotkey)

    for i in range(10):
        keyboard.add_hotkey(hotkeys['recognize_window'].format(i), lambda idx=i: recognize_specific_window(idx))

def capture_and_recognize_active_window(window_title):
    image = capture_window_screenshot(window_title)
    if image is None:
        return "Window not found."

    _, text_data = recognize_text_with_overlay(image)
    return "\n".join([f"{item['text']} at {item['coordinates']}" for item in text_data])

# Фоновый поток для горячих клавиш
hotkey_thread = threading.Thread(target=setup_hotkeys, daemon=True)
hotkey_thread.start()

if __name__ == '__main__':
    list_windows()
    app.run(debug=True)