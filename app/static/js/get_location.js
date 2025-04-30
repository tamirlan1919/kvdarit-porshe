// Функция для получения геолокации пользователя
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(sendLocation, showError);
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

// Функция для отправки геолокации на сервер
function sendLocation(position) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;

    // Отправка координат на сервер через POST-запрос
    fetch('/set_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            lat: lat,
            lon: lon
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Перенаправляем на главную страницу, если координаты приняты
            window.location.href = '/';
        } else {
            alert('Access denied or error occurred');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to send location data.');
    });
}

// Обработка ошибок, если геолокация не доступна или пользователь отказался
function showError(error) {
    switch(error.code) {
        case error.PERMISSION_DENIED:
            alert("User denied the request for Geolocation.");
            break;
        case error.POSITION_UNAVAILABLE:
            alert("Location information is unavailable.");
            break;
        case error.TIMEOUT:
            alert("The request to get user location timed out.");
            break;
        case error.UNKNOWN_ERROR:
            alert("An unknown error occurred.");
            break;
    }
}

// Вызов функции на загрузку страницы
window.onload = getLocation;