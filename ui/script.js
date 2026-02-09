const API_BASE_URL = 'http://localhost:8000';

// Элементы DOM
const urlInput = document.getElementById('urlInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const loading = document.getElementById('loading');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const filenameInput = document.getElementById('filenameInput');
const saveBtn = document.getElementById('saveBtn');
const analyzedUrlLink = document.getElementById('analyzedUrlLink');

// Элементы для результатов
const neuralClassic = document.getElementById('neuralClassic');
const neuralKeywords = document.getElementById('neuralKeywords');
const extractionClassic = document.getElementById('extractionClassic');
const extractionKeywords = document.getElementById('extractionKeywords');

// Обработчики событий
analyzeBtn.addEventListener('click', analyzeUrl);
saveBtn.addEventListener('click', saveResults);
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        analyzeUrl();
    }
});

async function analyzeUrl() {
    const url = urlInput.value.trim();

    if (!url) {
        showError('Пожалуйста, введите URL');
        return;
    }

    // Базовая валидация URL
    try {
        new URL(url);
    } catch {
        showError('Пожалуйста, введите корректный URL');
        return;
    }

    setLoading(true);
    hideError();
    hideResults();

    try {
        const response = await fetch(`${API_BASE_URL}/api/create-abstract?url=${encodeURIComponent(url)}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Error:', error);
        showError(`Ошибка при анализе URL: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

function displayResults(data) {
    // Устанавливаем URL как кликабельную ссылку
    analyzedUrlLink.href = data.url;
    analyzedUrlLink.textContent = data.url;

    // Заполняем результаты нейросети
    neuralClassic.textContent = data.neural_network.classic_abstract || 'Нет данных';
    neuralKeywords.innerHTML = formatKeywords(data.neural_network.keyword_abstract);

    // Заполняем результаты извлечения предложений
    extractionClassic.textContent = data.sentence_extraction.classic_abstract || 'Нет данных';
    extractionKeywords.innerHTML = formatExtractionKeywords(data.sentence_extraction.keyword_abstract);

    // Сохраняем данные для последующего сохранения
    currentResults = data;

    showResults();
}

function formatKeywords(keywords) {
    if (typeof keywords === 'string') {
        // Форматируем строку с ключевыми словами
        return keywords.replace(/\n/g, '<br>').replace(/\*/g, '•');
    }
    return keywords || 'Нет данных';
}

function formatExtractionKeywords(keywords) {
    if (Array.isArray(keywords)) {
        // Форматируем массив ключевых слов
        return keywords.map(word => `• ${word}`).join('<br>');
    } else if (typeof keywords === 'string') {
        return keywords;
    }
    return 'Нет данных';
}

async function saveResults() {
    const filename = filenameInput.value.trim();

    if (!filename) {
        showError('Пожалуйста, введите имя файла для сохранения');
        return;
    }

    if (!currentResults) {
        showError('Нет результатов для сохранения');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/save?filename=${encodeURIComponent(filename)}`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentResults)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result) {
            showSuccess(`Результаты успешно сохранены в файл: ${filename}.json`);
            filenameInput.value = '';
        }

    } catch (error) {
        console.error('Error:', error);
        showError(`Ошибка при сохранении: ${error.message}`);
    }
}

// Вспомогательные функции
function setLoading(isLoading) {
    if (isLoading) {
        loading.style.display = 'flex';
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Анализ...';
    } else {
        loading.style.display = 'none';
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Анализировать';
    }
}

function showResults() {
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function hideResults() {
    resultsSection.style.display = 'none';
}

function showError(message) {
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

function hideError() {
    errorSection.style.display = 'none';
}

function showSuccess(message) {
    // Создаем или находим элемент для успешного сообщения
    let successElement = document.querySelector('.success-message');
    if (!successElement) {
        successElement = document.createElement('div');
        successElement.className = 'success-message';
        saveBtn.parentNode.insertBefore(successElement, saveBtn.nextSibling);
    }

    successElement.textContent = message;
    successElement.style.display = 'block';

    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        successElement.style.display = 'none';
    }, 5000);
}

// Переменная для хранения текущих результатов
let currentResults = null;

// Пример URL для быстрого тестирования
urlInput.value = 'https://www.recipetineats.com/a-pumpkin-layer-cake-with-cream-cheese-frosting-and-toffee-pecans/';