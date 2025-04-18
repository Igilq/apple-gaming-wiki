const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('api', {
    fetch: async (url, options) => {
        console.log('Wysyłanie żądania:', url, options);
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            console.log('Otrzymano odpowiedź:', data);
            return data;
        } catch (error) {
            console.error('Błąd podczas żądania:', error);
            throw error;
        }
    }
});