const { contextBridge, ipcRenderer } = require('electron');

// Store the username from the last successful check
let lastUsername = null;

contextBridge.exposeInMainWorld('api', {
    fetch: async (url, options) => {
        console.log('Sending request:', url, options);
        try {
            const response = await fetch(url, options);

            // Check if response is ok and has content
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            // Check if response has content
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.warn('Response is not JSON, attempting to parse anyway');
            }

            // Check if response has content length
            const contentLength = response.headers.get('content-length');
            if (contentLength === '0') {
                console.warn('Response has empty body');
                return {}; // Return empty object for empty responses
            }

            // Clone the response before parsing to avoid "body already read" errors
            const clonedResponse = response.clone();

            try {
                const data = await response.json();
                console.log('Received response:', data);

                // Store username if it's in the response
                if (data && data.username) {
                    lastUsername = data.username;
                }

                return data;
            } catch (jsonError) {
                console.error('Error parsing JSON:', jsonError);

                // Try to get the text content for debugging
                const textContent = await clonedResponse.text();
                console.error('Response text content:', textContent);

                // Return empty object for invalid JSON
                return {};
            }
        } catch (error) {
            console.error('Error during request:', error);
            throw error;
        }
    },

    showSaveDialog: async (options) => {
        console.log('Showing save dialog with options:', options);
        try {
            return await ipcRenderer.invoke('show-save-dialog', options);
        } catch (error) {
            console.error('Error showing save dialog:', error);
            throw error;
        }
    },

    getUsername: () => {
        return { username: lastUsername };
    }
});
