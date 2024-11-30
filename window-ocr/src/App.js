import React, { useState } from "react";
import axios from "axios";

function App() {
  const [image, setImage] = useState(null); // Хранение изображения окна
  const [textData, setTextData] = useState([]); // Данные текста для отображения
  const [selectedWindow, setSelectedWindow] = useState(""); // Выбранное окно
  const [windows, setWindows] = useState([]); // Список окон

  // Функция для получения списка окон
  const fetchWindows = async () => {
    try {
      const response = await axios.get("http://localhost:5000/list_windows");
      setWindows(response.data); // Сохраняем список окон в состояние
    } catch (error) {
      console.error("Error fetching windows:", error);
    }
  };

  // Функция для распознавания текста в выбранном окне
  const recognizeText = async () => {
    if (!selectedWindow) {
      alert("Выберите окно!");
      return;
    }

    try {
      const response = await axios.post("http://localhost:5000/capture_and_recognize", {
        window_title: selectedWindow, // Отправляем выбранное окно на сервер
      });

      const { image: imgString, text_data } = response.data; // Извлекаем строку изображения и данные текста

      // Конвертируем строку изображения в формат, поддерживаемый React
      const imgSrc = `data:image/png;base64,${btoa(imgString)}`;

      setImage(imgSrc); // Обновляем состояние изображения
      setTextData(text_data); // Обновляем состояние с текстом
    } catch (error) {
      console.error("Error recognizing text:", error);
    }
  };

  return (
    <div style={{ textAlign: "center" }}>
      <h1>OCR Viewer</h1>

      {/* Кнопка для получения списка окон */}
      <button onClick={fetchWindows}>Получить список окон</button>

      {/* Список окон */}
      {windows.length > 0 && (
        <select
          onChange={(e) => setSelectedWindow(e.target.value)}
          value={selectedWindow}
        >
          <option value="">Выберите окно</option>
          {windows.map((title, idx) => (
            <option key={idx} value={title}>
              {title}
            </option>
          ))}
        </select>
      )}

      {/* Кнопка для распознавания текста */}
      <button onClick={recognizeText}>Распознать текст</button>
      <br></br>
      {/* Отображение изображения с наложением текста */}
      {image && (
        <div style={{ position: "relative", display: "inline-block" }}>
          <img
            src={image}
            alt="Window Screenshot"
            style={{ opacity: 0.5, maxWidth: "66%" }}
          />

          {/* Наложение текста на изображение */}
          {textData.map((item, idx) => {
            const { text, coordinates } = item;
            const { top_left, bottom_right } = coordinates;

            const style = {
              position: "absolute",
              left: top_left[0]/1.55+280,
              top: top_left[1]/1.5+10,
              backgroundColor: "rgba(255, 255, 255, 0.8)",
              padding: "2px 4px",
              borderRadius: "4px",
              transform: "translate(-50%, -50%)", // Центрируем текст
              whiteSpace: "nowrap",
            };

            return (
              <div
                key={idx}
                style={style}
                onClick={() => navigator.clipboard.writeText(text)} // Копирование текста в буфер обмена
              >
                {text}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default App;
